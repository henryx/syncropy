# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@ymail.com)
Project       Syncropy
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import logging
import logging.handlers
import src.protocols
import src.storage

class Sync(object):
    _cfg = None
    _mode = None

    def __init__(self, cfg):
        self._cfg = cfg

    def _set_log(self, filename, level):
        LEVELS = {'debug': logging.DEBUG,
                  'info': logging.INFO,
                  'warning': logging.WARNING,
                  'error': logging.ERROR,
                  'critical': logging.CRITICAL
                 }

        logger = logging.getLogger("Syncropy")
        logger.setLevel(LEVELS.get(level.lower(), logging.NOTSET))

        handler = logging.handlers.RotatingFileHandler(
                filename, maxBytes=20971520, backupCount=20)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = value

    @mode.deleter
    def mode(self):
        del self._mode

    def execute(self):
        protocols = {}
        fsstore = None
        dbstore = None

        fsstore = src.storage.FsStorage(self._cfg)
        dbstore = src.storage.DbStorage(self._cfg)

        fsstore.mode = self._mode
        dbstore.mode = self._mode

        sections = self._cfg.sections()
        sections.remove("general")
        sections.remove("database")

        dataset = dbstore.get_last_dataset()

        if dataset > self._cfg.getint("general", self.mode + "_grace"):
            dataset = 1
        else:
            dataset = dataset + 1

        self._set_log(filename=self._cfg.get("general", "log_file"),
                      level=self._cfg.get("general", "log_level"))
        logger = logging.getLogger("Syncropy")
        logger.info("Beginning backup")

        for item in sections:
            try:
                paths = self._cfg.get(item, "path").split(",")

                fsstore.section = item
                dbstore.section = item
                fsstore.dataset = dataset
                dbstore.dataset = dataset

                if self._cfg.get(item, "type") == "ssh":
                    ssh = SyncSSH(self._cfg)
                    ssh.section = item
                    ssh.filestore = fsstore
                    ssh.dbstore = dbstore
                    ssh.acl_sync = self._cfg.getboolean(item, "store_acl")

                    ssh.sync(paths)
            except Exception as (errno, strerror):
                self._logger.error("Error while retrieving data for" +
                                   section + ": " + strerror)
                
        dbstore.set_last_dataset(dataset)
        logger.info("Ending backup")

class SyncSSH(object):
    _cfg = None
    _remote = None

    _section = None
    _acl_sync = None
    _filestore = None
    _dbstore = None

    def __init__(self, cfg):
        self._cfg = cfg
        self._remote = src.protocols.SSH(self._cfg)

    def __del__(self):
        self._remote.close()

    def _get_item_list(self, path, itemtype):
        self._remote.send_cmd(
                        "find " +
                        path +
                        " -type " +
                        itemtype +
                        r" -exec stat --format='%a;%G;%U;%F;%Y;%Z;%n' \{\} + ")

        stdout = self._remote.get_stdout()
        return stdout

    def _get_item_attrs(self, item):
        result = {}

        result["permission"] = item.split(";")[0]
        result["group"] = item.split(";")[1]
        result["user"] = item.split(";")[2]

        if item.split(";")[3] == "directory":
            result["type"] = "d"
        elif item.split(";")[3] == "regular file":
            result["type"] = "f"
        else:
            result["type"] = "l"

        result["mtime"] = item.split(";")[4]
        result["ctime"] = item.split(";")[5]

        return result

    def _store(self, item):
        filedata = item.strip("\n").split(";/")

        fileitem = "/" + filedata[1]
        attrs = self._get_item_attrs(filedata[0])
        if attrs["type"] == "f" and self._dbstore.item_exist(fileitem, attrs):
            attrs["type"] = "pl"

        self._filestore.add(fileitem, attrs, self._remote)
        self._dbstore.add(fileitem, attrs)

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        self._section = value
        self._remote.connect(self.section)

    @section.deleter
    def section(self):
        del self._section

    @property
    def acl_sync(self):
        return self._acl_sync

    @acl_sync.setter
    def acl_sync(self, value):
        self._acl_sync = value

    @acl_sync.deleter
    def acl_sync(self):
        del self._acl_sync

    @property
    def filestore(self):
        return self._filestore

    @filestore.setter
    def filestore(self, value):
        self._filestore = value

    @filestore.deleter
    def filestore(self):
        del self._filestore

    @property
    def dbstore(self):
        return self._dbstore

    @dbstore.setter
    def dbstore(self, value):
        self._dbstore = value

    @dbstore.deleter
    def dbstore(self):
        del self._dbstore

    def sync(self, paths):
        if not self._filestore:
            raise AttributeError, "Filestore not definied"

        if not self._dbstore:
            raise AttributeError, "Dbstore not definied"

        if not self._section:
            raise AttributeError, "Section not definied"

        for path in paths:
            stdout = self._get_item_list(path, "d")
            for remote_item in stdout.readlines():
                self._store(remote_item)

            stdout = self._get_item_list(path, "f")
            for remote_item in stdout.readlines():
                self._store(remote_item)