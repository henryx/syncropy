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

    def _get_attrs(self, item, protocol):
        data = {}
        
        protocol.send_cmd(r"stat --format='%a;%G;%U' " + item)
        # Spaghetti code?
        item = protocol.get_stdout().readlines()[0].strip("\n").split(";")
        
        data["permission"] = item[0]
        data["group"] = item[1]
        data["user"] = item[2]
        
        return data

    def execute(self):
        protocol = None
        store = None
        dbstore = None

        sections = self._cfg.sections()
        sections.remove("general")
        sections.remove("database")

        for item in sections:
            paths = self._cfg.get(item, "path").split(",")

            if self._cfg.get(item, "type") == "ssh":
                protocol = src.protocols.SSH(self._cfg)

                store = src.storage.FsStorage(self._cfg)
                dbstore = src.storage.DbStorage(self._cfg)

                store.mode = self._mode
                dbstore.mode = self._mode

                dataset = dbstore.get_last_dataset()

                if dataset > self._cfg.getint("general", self.mode + "_grace"):
                    dataset = 1
                else:
                    dataset = dataset + 1

                protocol.connect(item)
                store.section = item
                dbstore.section = item
                store.dataset = dataset
                dbstore.dataset = dataset

                for path in paths:
                    protocol.send_cmd("find " + path + " -type d")
                    for remote_item in protocol.get_stdout().readlines():
                        store.add_dir(remote_item)
                        dbstore.add_item(remote_item, "d")
                        attrs = self._get_attrs(remote_item, protocol)
                        dbstore.add_attrs(remote_item, "d", attrs)

                protocol.close()

        dbstore.set_last_dataset(dataset)
