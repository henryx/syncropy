# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (server module)
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import logging

import storage
import sync
from multiprocessing import Pool

class Common(object):
    _cfg = None
    _grace = None
    _dataset = None

    def __init__(self, cfg):
        self._cfg = cfg

    @property
    def grace(self):
        return self._grace

    @grace.setter
    def grace(self, value):
        self._grace = value

    @grace.deleter
    def grace(self):
        del self._grace

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, value):
        self._dataset = value

    @dataset.deleter
    def dataset(self):
        del self._dataset

class Sync(Common):
    def __init__(self, cfg):
        super(Sync, self).__init__(cfg)
        # NOTE: property dataset is not used in this class

    def execute(self):
        sections = self._cfg.sections()

        for section in ["general", "dataset", "database"]:
            sections.remove(section)

        dataset = storage.db_get_last_dataset(self._cfg, self._grace)

        if (dataset + 1) > self._cfg.getint("dataset", self._grace):
            dataset = 1
        else:
            dataset = dataset + 1

        logger = logging.getLogger("Syncropy")
        logger.info("Started backup")

        pool = Pool(5) # NOTE: maximum concurrent processes is hardcoded for convenience
        for section in sections:
            fsstore = storage.Filesystem(self._cfg)

            fsstore.grace = self._grace
            fsstore.dataset = dataset
            fsstore.section = section

            if self._cfg.get(section, "type") == "file":
                filesync = sync.FileSync(self._cfg)
                filesync.section = section
                filesync.filestore = fsstore

                pool.apply_async(filesync.start)
        pool.close()
        pool.join()

class Remove(Common):
    def __init__(self, cfg):
        super(Remove, self).__init__(cfg)

    def execute(self):
        pass
