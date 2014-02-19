# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (server module)
License       GPL version 2 (see GPL.txt for details)
"""
import logging
import multiprocessing

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
import pickle
import socket
import ssl

import storage

class Common(object):
    _cfg = None
    _section = None
    _grace = None
    _dataset = None

    def __init__(self, cfg):
        self._cfg = pickle.loads(cfg)

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        if not self._dataset:
            raise AttributeError("Dataset not defined")

        self._section = pickle.loads(value)

    @section.deleter
    def section(self):
        del self._section

    @property
    def grace(self):
        return self._grace

    @grace.setter
    def grace(self, value):
        self._grace = pickle.loads(value)

    @grace.deleter
    def grace(self):
        del self._grace

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, value):
        if not self._grace:
            raise AttributeError("Grace not defined")

        self._dataset = pickle.loads(value)

    @dataset.deleter
    def dataset(self):
        del self._dataset

class FileSync(Common):
    _filestore = None

    def __init__(self, cfg):
        super(FileSync, self).__init__(cfg)

    @property
    def filestore(self):
        return self._filestore

    @filestore.setter
    def filestore(self, value):
        self._filestore = pickle.loads(value)

    @filestore.deleter
    def filestore(self):
        del self._filestore

    def start(self):
        section = {
            "name": self.section,
            "grace": self.grace,
            "dataset": self.dataset,
            "compressed": False # TODO: get parameter from configuration file (for future implementation)
        }

        cmdlist = {
            "context": "file",
            "command": {
                "name": "list",
                "directory": self._cfg.get(self._section, "path").split(","),
                "acl": self._cfg.getboolean(self._section, "acl")
            }
        }
        logger = logging.getLogger("Syncropy")

        with storage.Database(self._cfg) as dbs:
            storage.db_del_dataset(dbs, section)
        logger.debug(self._section + ": Database cleaned")

        storage.fs_remove_dataset(self._cfg, section)
        logger.debug(self._section + ": Dataset tree section removed")

        if self._cfg.getboolean(self._section, "ssl"):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.load_cert_chain(
                certfile=self._cfg.get(self._section, "sslcert"),
                keyfile=self._cfg.get(self._section, "sslkey"),
                password=self._cfg.get(self._section, "sslpass")
            )

            conn = context.wrap_socket(sock)
        else:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        logger.debug(self._section + ": Socket created")
        conn.connect((self._cfg.get(self._section, "host"), self._cfg.getint(self._section, "port")))
        logger.debug(self._section + ": Socket connected")
        conn.send(json.dumps(cmdlist).encode("utf-8"))
        logger.debug(self._section + ": JSON command list sended")

        with storage.Database(self._cfg) as dbs:
            while True:
                data = conn.read()

                if not data:
                    break

                response = json.loads(data.decode("utf-8"))
                storage.db_save_attrs(dbs, section, response)
                if response["attrs"]["type"] == "directory":
                    storage.fs_add(self._cfg, section, response["name"], response["attrs"]["type"])
            logger.debug(self._section + ": JSON list readed")

            for item in storage.db_list_items(dbs, section, "file"):
                # TODO: Add code for getting files
                pass
        conn.close()
        logger.debug(self._section + ": Sync done")