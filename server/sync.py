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
import pickle
import socket
import ssl
import sys
from contextlib import closing

import storage

def get_remote_conn(cfg, section):
    logger = logging.getLogger("Syncropy")
    if cfg[section].getboolean("ssl"):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        try:
            context.load_cert_chain(
                certfile=cfg[section]["sslpem"],
                password=cfg[section]["sslpass"]
            )
        except FileNotFoundError:
            logger.fatal("PEM key not found in " + cfg[section]["sslpem"])
            sys.exit(4)

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

    with closing(get_remote_conn(cfg, section["name"])) as conn, storage.Database(cfg) as dbs:
        conn.send(json.dumps(cmdlist).encode("utf-8"))
        logger.debug(section["name"] + ": JSON command list sended")

        f = conn.makefile()
        for data in f:
            response = json.loads(data)
            storage.db_save_attrs(dbs, section, response)

        logger.debug(section["name"] + ": JSON list readed")

def fs_get_data(cfg, section):
    if (section["dataset"] - 1) == 0:
        previous = int(cfg["dataset"][section["grace"]])
    else:
        previous = section["dataset"] - 1

    with storage.Database(cfg) as dbs:
        for item in storage.db_list_items(dbs, section, "directory"):
            try:
                storage.fs_save(cfg, section, item)
            except FileExistsError:
                pass
        for item in storage.db_list_items(dbs, section, "file"):
            if storage.db_item_exist(dbs, section, item, previous):
                storage.fs_save(cfg, section, item, previous=True)
            else:
                with closing(get_remote_conn(cfg, section["name"])) as conn:
                    storage.fs_save(cfg, section, item, conn=conn)

        for item in storage.db_list_items(dbs, section, "symlink"):
                storage.fs_save(cfg, section, item)

def fs_start(conf, process):
    error = False

    def exec_remote_cmd(command):
        if not command == "":
            execmd ={
                "context": "system",
                "command": {
                    "name": "exec",
                    "value": command
                }
            }
            with closing(get_remote_conn(cfg, section["name"])) as conn:
                conn.send(json.dumps(execmd).encode("utf-8"))

                f = conn.makefile()
                for data in f:
                    response = json.loads(data)
                    if response["result"] == "ko":
                        raise Exception("Remote command error: " + response["message"])

    cfg = pickle.loads(conf)
    section = pickle.loads(process)
    logger = logging.getLogger("Syncropy")

    logger.info("About to execute " + section["name"])

    if "pre_command" in cfg[section["name"]]:
        try:
            exec_remote_cmd(cfg[section["name"]]["pre_command"])
        except Exception as err:
            logger.error("Pre command for {0} failed: {1}".format(section["name"], err))
            logger.exception("Exception Traceback")
            error = True

    if not error:
        try:
            fs_get_metadata(cfg, section)
            fs_get_data(cfg, section)
        except Exception as err:
            logger.error("Sync for {0} failed: {1}".format(section["name"], err))
            logger.exception("Exception Traceback")

    if "post_command" in cfg[section["name"]]:
        try:
            exec_remote_cmd(cfg[section["name"]]["post_command"])
        except Exception as err:
            logger.error("Post command for {0} failed: {1}".format(section["name"], err))
            logger.exception("Exception Traceback")

    logger.debug(section["name"] + ": Sync done")