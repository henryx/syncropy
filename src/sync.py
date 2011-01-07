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

    def _sync_ssh(self, paths, acl_store, protocol, store, dbstore):
        for path in paths:
            protocol.send_cmd("find " + path + " -type d")
            for remote_item in protocol.get_stdout().readlines():
                attrs = self._get_item_attrs(remote_item.strip("\n"), "d", acl_store, protocol)
                if attrs:
                    store.add_dir(remote_item.strip("\n"))
                    dbstore.add_element(remote_item.strip("\n"), "d", attrs)
                    dbstore.add_attrs(remote_item.strip("\n"), "d", attrs)

            protocol.send_cmd("find " + path + " -type f")
            for remote_item in protocol.get_stdout().readlines():
                attrs = self._get_item_attrs(remote_item.strip("\n"), "f", acl_store, protocol)
                if attrs:
                    if dbstore.item_exist(remote_item.strip("\n"), attrs):
                        store.add_item(remote_item.strip("\n"), protocol, "l")
                    else:
                        store.add_item(remote_item.strip("\n"), protocol, "f")
                    dbstore.add_element(remote_item.strip("\n"), "f", attrs)
                    dbstore.add_attrs(remote_item.strip("\n"), "f", attrs)

    def _get_item_attrs(self, item, item_type, acl_store, protocol):
        data = {}
        acls = []
        
        protocol.send_cmd(r"stat --format='%a;%G;%U' " + item)

        if not protocol.is_err_cmd():
            for res in protocol.get_stdout().readlines():
                data["permission"] = res.strip("\n").split(";")[0]
                data["group"] = res.strip("\n").split(";")[1]
                data["user"] = res.strip("\n").split(";")[2]
        
            if item_type == "f":
                protocol.send_cmd(r"md5sum " + item)
                res = protocol.get_stdout().readlines()[0].strip("\n")
                data["hash"] = res.split(" ")[0]
        """
        if acl_store:
            protocol.send_cmd(r"getfacl " + item)

            if not protocol.is_err_cmd():
                for res in protocol.get_stdout().readlines():
                    if not res.strip("\n").startswith("#"):
                        acls.append(res.strip("\n"))
        """
        return data

    def execute(self):
        protocol = None
        store = None
        dbstore = None

        store = src.storage.FsStorage(self._cfg)
        dbstore = src.storage.DbStorage(self._cfg)

        sections = self._cfg.sections()
        sections.remove("general")
        sections.remove("database")

        store.mode = self._mode
        dbstore.mode = self._mode

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
                
                if self._cfg.getboolean(item, "store_acl"):
                    acl_store = True
                else:
                    acl_store = False
                
                protocol = src.protocols.SSH(self._cfg)

                protocol.connect(item)
                self._sync_ssh(paths, acl_store, protocol, store, dbstore)
                
                protocol.close()

        dbstore.set_last_dataset(dataset)
