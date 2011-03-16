# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import src.protocols
import src.storage

class Sync(object):
    _cfg = None
    _mode = None

    def __init__(self, cfg):
        self._cfg = cfg

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
        store = None
        dbstore = None

        store = src.storage.FsStorage(self._cfg)
        dbstore = src.storage.DbStorage(self._cfg)

        store.mode = self._mode
        dbstore.mode = self._mode

        sections = self._cfg.sections()
        sections.remove("general")

        dataset = dbstore.get_last_dataset()

        if dataset > self._cfg.getint("general", self.mode + "_grace"):
            dataset = 1
        else:
            dataset = dataset + 1

        for item in sections:
            paths = self._cfg.get(item, "path").split(",")

            store.section = item
            dbstore.section = item
            store.dataset = dataset
            dbstore.dataset = dataset

            if self._cfg.get(item, "type") == "ssh":
                ssh = SyncSSH(self._cfg)
                ssh.section = item
                ssh.filestore = store
                ssh.dbstore = dbstore

                if self._cfg.getboolean(item, "store_acl"):
                    ssh.acl_sync = True
                else:
                    ssh.acl_sync = False

                ssh.sync(paths)

        dbstore.set_last_dataset(dataset)

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
            result.put("type", "d")
        elif item.split(";")[3] == "regular file":
            result.put("type", "f")
        else:
            result.put("type", "l")

        result["mtime"] = item.split(";")[4]
        result["chtime"] = item.split(";")[5]

        return result

    def _store(self, item):
        filedata = item.strip("\n").split(";/")

        fileitem = "/" + filedata[1]
        attrs = self._get_item_attrs(filedata[0])
        if attrs["type"] == "f" and self._dbstore.item_exist():
            attrs["type"] = "pl"

        self._filestore.add(fileitem, attrs)
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