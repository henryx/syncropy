# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import itertools
#import logging
import logging.handlers
#import sys

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
        #protocols = {}
        fsstore = None
        dbstore = None

        fsstore = src.storage.FsStorage(self._cfg)
        dbstore = src.storage.DbStorage(self._cfg)

        fsstore.mode = self._mode
        dbstore.mode = self._mode

        self._set_log(filename=self._cfg.get("general", "log_file"),
                      level=self._cfg.get("general", "log_level"))
        logger = logging.getLogger("Syncropy")
        logger.info("Beginning backup")

        sections = self._cfg.sections()
        sections.remove("general")
        sections.remove("database")

        dataset = dbstore.get_last_dataset()

        if dataset >= self._cfg.getint("general", self.mode + "_grace"):
            dataset = 1
        else:
            dataset = dataset + 1

        logger.debug("Last dataset for mode " + self.mode + ": " +str(dataset))

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
            except Exception as ex:
                logger.error("Error while retrieving data for " +item)
                for error in ex:
                    if type(error) == str:
                        logger.error("    " + error)
                    else:
                        for line in error:
                            logger.error("    " + line)

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

    def _get_list_item(self, path, itemtype):
        self._remote.send_cmd(
                        "find " +
                        path +
                        " -type " +
                        itemtype +
                        r" -print0 | xargs -0 stat --format='%a;%G;%U;%F;%Y;%Z;%n'")

        stdout = self._remote.get_stdout()
        return stdout

    def _get_list_acl(self, path):
        self._remote.send_cmd(
                        "find " +
                        path +
                        r" -print0 | xargs -0 getfacl")

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

    def _get_item_acl(self, item):
        result = {}
        name = ""
        user = []
        group = []

        for line in item:
            if line[:6] == "# file":
                name = "/" + line[8:].strip("\n")
            elif line[:4] == "user" and line[4:6] != "::":
                    perms = {}
                    perms["uid"] = line.split(":")[1]
                    perms["attrs"] = line.split(":")[2].strip("\n")
                    user.append(perms)
            elif line[:5] == "group" and line[5:7] != "::":
                    perms = {}
                    perms["gid"] = line.split(":")[1]
                    perms["attrs"] = line.split(":")[2].strip("\n")
                    group.append(perms)

        result["name"] = name
        result["user"] = user
        result["group"] = group

        return result

    def _store_item(self, item):
        filedata = item.strip("\n").split(";/")

        fileitem = "/" + filedata[1]
        attributes = self._get_item_attrs(filedata[0])
        if attributes["type"] == "f" and self._dbstore.item_exist(fileitem, attributes):
            attributes["type"] = "pl"

        self._filestore.add(fileitem, attributes, self._remote)
        self._dbstore.add(fileitem, attrs=attributes)

    def _store_acl(self, item):
        acl = self._get_item_acl(item)
        self._dbstore.add(acl["name"], acls=acl)

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

        if self._cfg.get(self._section, "pre_command") != "":
            self._remote.send_cmd(self._cfg.get(self._section, "pre_command"))
            if self._remote.is_err_cmd():
                raise Exception(self._remote.get_errstr())

        for path in paths:
            dirs = self._get_list_item(path, "d")
            files = self._get_list_item(path, "f")

            if self.acl_sync:
                acls = self._get_list_acl(path)
            else:
                acls = []

            for remote_item in dirs.readlines():
                self._store_item(remote_item)

            for remote_item in files.readlines():
                self._store_item(remote_item)

            while True:
                acl = list(itertools.takewhile(lambda x: x != "\n", acls))
                if len(acl) == 0:
                    break
                self._store_acl(acl)

        if self._cfg.get(self._section, "post_command") != "":
            self._remote.send_cmd(self._cfg.get(self._section, "post_command"))
            if self._remote.is_err_cmd():
                raise Exception(self._remote.get_errstr())
