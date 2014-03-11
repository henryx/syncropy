# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (server module)
License       GPL version 2 (see GPL.txt for details)
"""

"""
NOTE:

Grace:
    Hourly backup;
    Daily backup;
    Weekly backup;
    Monthly backup

Dataset:
    An incremental for grace backup

Section:
    A machine that backup

"""

__author__ = "enrico"

import json
import logging
import os
import pickle
import socket
import ssl
from contextlib import closing

import storage

def fs_get_conn(cfg, section):
    logger = logging.getLogger("Syncropy")
    if cfg[section].getboolean("ssl"):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.load_cert_chain(
            certfile=cfg[section]["sslpem"],
            password=cfg[section]["sslpass"]
        )

        conn = context.wrap_socket(sock)
    else:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logger.debug(section + ": Socket created")

    conn.connect((cfg[section]["host"], int(cfg[section]["port"])))
    logger.debug(section + ": Socket connected")

    return conn

def fs_get_metadata(cfg, section):
    logger = logging.getLogger("Syncropy")
    cmdlist = {
        "context": "file",
        "command": {
            "name": "list",
            "directory": cfg[section["name"]]["path"].split(","),
            "acl": cfg[section["name"]].getboolean("acl")
        }
    }

    with closing(fs_get_conn(cfg, section["name"])) as conn, storage.Database(cfg) as dbs:
        conn.send(json.dumps(cmdlist).encode("utf-8"))
        logger.debug(section["name"] + ": JSON command list sended")

        f = conn.makefile()
        for data in f:
            response = json.loads(data)
            storage.db_save_attrs(dbs, section, response)
            if response["attrs"]["type"] == "directory":
                storage.fs_create_dir(cfg, section, response["name"])

        logger.debug(section["name"] + ": JSON list readed")


def fs_get_data(cfg, section):
    if (section["dataset"] - 1) == 0:
        previous = int(cfg["dataset"][section["grace"]])
    else:
        previous = section["dataset"] - 1

    with storage.Database(cfg) as dbs:
        for item in storage.db_list_items(dbs, section, "file"):
            if storage.db_item_exist(dbs, section, item, previous):
                os.link(os.sep.join([storage.fs_compute_destination(cfg, section, True), item[0]]),
                        os.sep.join([storage.fs_compute_destination(cfg, section, False), item[0]]))
            else:
                with closing(fs_get_conn(cfg, section["name"])) as conn:
                    storage.fs_save_file(cfg, section, item[0], conn)

def fs_start(conf, process):
    cfg = pickle.loads(conf)
    section = pickle.loads(process)
    logger = logging.getLogger("Syncropy")

    logger.info("About to execute " + section["name"])

    if "pre_command" in cfg[section["name"]]:
        if not cfg[section["name"]]["pre_command"] == "":
            execmd ={
                "context": "system",
                "command": {
                    "name": "exec",
                    "value": cfg[section["name"]]["pre_command"]
                }
            }
            with closing(fs_get_conn(cfg, section["name"])) as conn:
                conn.send(json.dumps(execmd).encode("utf-8"))

    with storage.Database(cfg) as dbs:
        storage.db_del_dataset(dbs, section)
    logger.debug(section["name"] + ": Database cleaned")

    storage.fs_remove_dataset(cfg, section)
    logger.debug(section["name"] + ": Dataset tree section removed")

    fs_get_metadata(cfg, section)
    fs_get_data(cfg, section)

    if "post_command" in cfg[section["name"]]:
        if not cfg[section["name"]]["post_command"] == "":
            execmd ={
                "context": "system",
                "command": {
                    "name": "exec",
                    "value": cfg[section["name"]]["post_command"]
                }
            }
            with closing(fs_get_conn(cfg, section["name"])) as conn:
                conn.send(json.dumps(execmd).encode("utf-8"))

    logger.debug(section["name"] + ": Sync done")