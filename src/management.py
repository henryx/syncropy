# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import logging

import src.storage
import src.sync

class Common(object):
    _cfg = None
    _mode = None
    _fsstore = None
    _dbstore = None

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

class Sync(Common):
    _reload = None

    def __init__(self, cfg):
        super(Sync, self).__init__(cfg)

    @property
    def dataset_reload(self):
        return self._reload

    @dataset_reload.setter
    def dataset_reload(self, value):
        self._reload = value

    @dataset_reload.deleter
    def dataset_reload(self):
        del self._reload

    def execute(self):
        fsstore = src.storage.FsStorage(self._cfg)
        dbstore = src.storage.DbStorage(self._cfg)

        fsstore.mode = self._mode
        dbstore.mode = self._mode

        logger = logging.getLogger("Syncropy")

        sections = self._cfg.sections()
        sections.remove("general")
        sections.remove("database")

        logger.info("Beginning backup")
        dataset = dbstore.get_last_dataset()
        if not self._reload:
            if dataset >= self._cfg.getint("general", self.mode + "_grace"):
                dataset = 1
            else:
                dataset = dataset + 1

        logger.debug("Last dataset for mode " + self.mode + ": " + str(dataset))

        fsstore.dataset = dataset
        dbstore.dataset = dataset

        rem = Remove(self._cfg)
        rem.mode = self._mode
        rem.dataset = dataset
        rem.execute()

        for item in sections:
            try:
                paths = self._cfg.get(item, "path").split(",")

                fsstore.section = item
                dbstore.section = item

                if self._cfg.get(item, "type") == "ssh":
                    ssh = src.sync.SyncSSH(self._cfg)
                    ssh.section = item
                    ssh.filestore = fsstore
                    ssh.dbstore = dbstore
                    ssh.acl_sync = self._cfg.getboolean(item, "store_acl")

                    ssh.sync(paths)
            except Exception as ex:
                logger.error("Error while retrieving data for " +item)
                for error in ex:
                    if type(error) in [str, int, long]:
                        logger.error("    " + str(error))
                    else:
                        for line in error:
                            logger.error("    " + line)

        dbstore.set_last_dataset(dataset)
        logger.info("Ending backup")

class Remove(Common):
    _dataset = None

    def __init__(self, cfg):
        super(Remove, self).__init__(cfg)

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, value):
        self._dataset = value

    @dataset.deleter
    def dataset(self):
        del self._dataset

    def execute(self):
        fsstore = src.storage.FsStorage(self._cfg)
        dbstore = src.storage.DbStorage(self._cfg)

        fsstore.mode = self._mode
        dbstore.mode = self._mode

        fsstore.dataset = self._dataset
        dbstore.dataset = self._dataset

        if fsstore.check_dataset_exist():
            fsstore.remove_dataset()

        if dbstore.check_dataset_exist():
            dbstore.remove_dataset()

class Info(Common):
    _dataset = None
    
    def __init__(self, cfg):
        super(Info, self).__init__(cfg)

    @property
    def dataset(self):
        dbstore = src.storage.DbStorage(self._cfg)

        dbstore.mode = self._mode
        self._dataset = dbstore.get_last_dataset()

        return self._dataset

    @dataset.deleter
    def dataset(self):
        del self._dataset