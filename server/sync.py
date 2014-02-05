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
import socket
import ssl

class Common(object):
    _cfg = None
    _section = None
    _dbstore = None
    _filestore = None

    def __init__(self, cfg):
        self._cfg = cfg

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        self._section = value

    @section.deleter
    def section(self):
        del self._section

    @property
    def filestore(self):
        return self._filestore

    @filestore.setter
    def filestore(self, value):
        self._filestore = value

    @filestore.deleter
    def filestore(self):
        del self._filestore

class FileSync(Common):
    def __init__(self, cfg):
        super(FileSync, self).__init__(cfg)

    def start(self):
        cmd = {
            "context": "file",
            "command": {
                "name": "list",
                "directory": self._cfg.get(self._section, "path").split(","),
                "acl": self._cfg.getboolean(self._section, "acl")
            }
        }

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

        conn.connect((self._cfg.get(self._section, "host"), self._cfg.getint(self._section, "port")))
        conn.send(json.dumps(cmd).encode("utf-8"))

        while True:
            data = conn.read()

            if not data:
                break
            print(data) # NOTE: For testing only
        print("Done") # NOTE: For testing only

