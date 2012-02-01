# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (server module)
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import logging
import os

class Database(object):
    _cfg = None

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

        if not self._mode:
            raise AttributeError("Dataset not definied")

    @dataset.deleter
    def dataset(self):
        del self._dataset

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        self._section = value

    @section.deleter
    def section(self):
        del self._section

class Filesystem(object):
    _cfg = None
    _logger = None
    _repository = None

    def __init__(self, cfg):
        self._cfg = cfg
        self._repository = self._cfg.get("general", "repository")

        self._logger = logging.getLogger("Syncropy")

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
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        self._section = value

        if not os.path.exists("/".join([self._cfg.get("general", "repository"),
                                 self._mode,
                                 str(self._dataset),
                                 self._section])):
            os.makedirs("/".join([self._cfg.get("general", "repository"),
                                 self._mode,
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
        self._dataset = value

        if not self._mode:
            raise AttributeError("Grace not definied")

    @dataset.deleter
    def dataset(self):
        del self._dataset
