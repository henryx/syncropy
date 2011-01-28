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
        sections.remove("database")

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
    _protocols = None

    _section = None
    _acl_sync = None
    _filestore = None
    _dbstore = None

    def __init__(self, cfg):
        self._cfg = cfg
        self._protocols = {}

    def __del__(self):
        for item in self._protocols.keys():
            self._protocols[item].close()

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        self._section = value

        self._protocols[self._section + "data"] = src.protocols.SSH(self._cfg)
        self._protocols[self._section + "attrs"] = src.protocols.SSH(self._cfg)
        self._protocols[self._section + "hash"] = src.protocols.SSH(self._cfg)

        for item in self._protocols.keys():
            self._protocols[item].connect(self.section)

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
            self._protocols[self._section + "data"].send_cmd("find " + path + " -type d")
            stdout = self._protocols[self._section + "data"].get_stdout()

            for remote_item in stdout.readlines():
                attrs = self._get_item_attrs(remote_item.strip("\n"), "d")
                if attrs:
                    self._filestore.add_dir(remote_item.strip("\n"))
                    self._dbstore.add_element(remote_item.strip("\n"), "d", attrs)
                    self._dbstore.add_attrs(remote_item.strip("\n"), "d", attrs)

                self._protocols[self._section + "data"].send_cmd("find " + path + " -type f")
                stdout = self._protocols[self._section + "data"].get_stdout()

                for remote_item in stdout.readlines():
                    attrs = self._get_item_attrs(remote_item.strip("\n"), "f")
                    if attrs:
                        if self._dbstore.item_exist(remote_item.strip("\n"), attrs):
                            self.filestore.add_item(remote_item.strip("\n"),
                                                    self._protocols[self._section + "data"],
                                                    "l")
                        else:
                            self.filestore.add_item(remote_item.strip("\n"),
                                                    self._protocols[self._section + "data"],
                                                    "f")
                        self._dbstore.add_element(remote_item.strip("\n"), "f", attrs)
                        self._dbstore.add_attrs(remote_item.strip("\n"), "f", attrs)

    def _get_item_attrs(self, item, item_type):
        data = {}
        acls = []

        remote_cmd = r"stat --format='%a;%G;%U' '" + item + "'"
        #print remote_cmd
        self._protocols[self._section + "attrs"].send_cmd(remote_cmd)

        if not self._protocols[self._section + "attrs"].is_err_cmd():
            stdout = self._protocols[self._section + "attrs"].get_stdout()

            for res in stdout.readlines():
                data["permission"] = res.strip("\n").split(";")[0]
                data["group"] = res.strip("\n").split(";")[1]
                data["user"] = res.strip("\n").split(";")[2]

            if item_type == "f":
                remote_cmd = r"md5sum '" + item + "'"
                self._protocols[self._section + "hash"].send_cmd(remote_cmd)
                stdout = self._protocols[self._section + "hash"].get_stdout()
                for item in stdout.readlines():
                    res = item[0].strip("\n")
                    data["hash"] = res.split(" ")[0]
        """
        if self._acl_sync:
            remote_cmd = r"getfacl '" + item + "'"
            protocol.send_cmd(remote_cmd)

            if not protocol.is_err_cmd():
                for res in protocol.get_stdout().readlines():
                    if not res.strip("\n").startswith("#"):
                        acls.append(res.strip("\n"))
        """
        return data