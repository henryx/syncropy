# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (server module)
License       GPL version 2 (see GPL.txt for details)
"""

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


__author__ = "enrico"

import logging
import os
import pymongo

class Database(object):
    _cfg = None
    _conn = None
    _db = None
    _grace = None
    _dataset = None
    _section = None

    def __init__(self, cfg):
        self._cfg = cfg

        self._conn = pymongo.Connection(self._cfg.get("database", "host"), self._cfg.getint("database", "port"))
        self._db = self.conn[self._cfg.get("database", "name")]

    @property
    def grace(self):
        return self._grace

    @grace.setter
    def grace(self, value):
        if not value in self._db.collection_names():
            self._grace = self._db[self._grace]
            self._grace.save({"status": 0})

    @grace.deleter
    def grace(self):
        del self._grace

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, value):
        if not self._grace:
            raise AttributeError("Grace not definied")

        self._dataset = self._db[self._grace][value]

    @dataset.deleter
    def dataset(self):
        del self._dataset

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        if not self._dataset:
            raise AttributeError("Dataset not definied")

        self._section = self._dataset[value]

    @section.deleter
    def section(self):
        del self._section

    def add(self):
        pass

class Filesystem(object):
    _cfg = None
    _logger = None
    _repository = None

    def __init__(self, cfg):
        self._cfg = cfg
        self._repository = self._cfg.get("general", "repository")

        self._logger = logging.getLogger("Syncropy")

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
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        self._section = value

        if not os.path.exists(os.sep.join([self._cfg.get("general", "repository"),
                                 self._grace,
                                 str(self._dataset),
                                 self._section])):
            os.makedirs(os.sep.join([self._cfg.get("general", "repository"),
                                 self._grace,
                                 str(self._dataset),
                                 self._section]))

    @section.deleter
    def section(self):
        del self._section

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, value):
        if not self._grace:
            raise AttributeError("Grace not definied")

        self._dataset = value

    @dataset.deleter
    def dataset(self):
        del self._dataset
        
    def add(self):
        pass