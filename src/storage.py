# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import os
import shutil
import src.db

class Storage(object):
    _cfg = None
    _repository = None
    
    _mode = None
    _dataset = None
    _section = None

    def __init__(self, cfg):
        self._cfg = cfg
        self._repository = self._cfg.get("general", "repository")
        
        self._check_structure()

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
        
        if not self._section:
            raise AttributeError, "Section not definied"
        
        if not self._mode:
            raise AttributeError, "Mode not definied"
        
        path = "/".join([self._repository, self._mode, str(self._dataset), self._section])

        if os.path.exists(path):
            self._remove_dataset(path, self._dataset)
        
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

    def _remove_dataset(self, path, dataset):
        shutil.rmtree(path)
        # TODO: remove dataset from database

    def _check_structure(self):
        if not os.path.exists(self._repository):
            os.mkdir(self._repository)
            os.mkdir(self._repository + "/hour")
            os.mkdir(self._repository + "/day")
            os.mkdir(self._repository + "/week")
            os.mkdir(self._repository + "/month")

    def _gen_prev_dataset(self, path):
        if self.dataset - 1 == 0:
            prev_dataset = self._cfg.getint("general", self._mode + "_grace")
        else:
            prev_dataset = self.dataset - 1

        return "/".join([self._repository, self._mode,
                         str(prev_dataset), self._section, path.strip("\n")])

    def create_dirs(self, stdout):
        for item in stdout.readlines():
            path = "/".join([self._repository, self._mode,
                              str(self.dataset), self._section, item.strip("\n")])
            os.makedirs(path)
