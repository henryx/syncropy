# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (server module)
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import logging
import pickle
import sync

import storage

from concurrent.futures import ProcessPoolExecutor

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

        with ProcessPoolExecutor(max_workers=5) as pool: # NOTE: maximum concurrent processes is hardcoded for convenience
            for section in sections:
                if self._cfg.get(section, "type") == "file":
                    filesync = sync.FileSync(pickle.dumps(self._cfg))

                    filesync.grace = pickle.dumps(self._grace)
                    filesync.dataset = pickle.dumps(dataset)
                    filesync.section = pickle.dumps(section)

                    pool.submit(filesync.start)

        storage.db_set_last_dataset(self._cfg, self.grace, dataset)

class Remove(Common):
    def __init__(self, cfg):
        super(Remove, self).__init__(cfg)

    def execute(self):
        pass
