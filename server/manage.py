 
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
        dbstore = storage.Database(self._cfg)
        fsstore = storage.Filesystem(self._cfg)

        fsstore.grace = self._grace
        dbstore.grace = self._grace

        sections = self._cfg.sections()

        for section in ["general", "dataset", "database"]:
            sections.remove(section)

        dataset = dbstore.get_last_dataset()

        if (dataset + 1) > self._cfg.getint("dataset", self._grace):
            dataset = 1
        else:
            dataset = dataset + 1

        logger = logging.getLogger("Syncropy")
        logger.info("Beginning backup")

class Remove(Common):
    def __init__(self, cfg):
        super(Remove, self).__init__(cfg)

    def execute(self):
        pass
