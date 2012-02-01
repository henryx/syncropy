 
# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (server module)
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import storage

class Common(object):
    _cfg = None
    _mode = None
    _dataset = None

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

        fsstore.mode = self._mode
        dbstore.mode = self._mode

        sections = self._cfg.sections()

        for section in ["general", "dataset"]:
            sections.remove(section)

        logger = logging.getLogger("Syncropy")
        logger.info("Beginning backup")

class Remove(Common):
    def __init__(self, cfg):
        super(Remove, self).__init__(cfg)

    def execute(self):
        pass
