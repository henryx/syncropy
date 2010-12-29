# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import os

class Storage(object):
    _cfg = None
    _repository = None
    mode = None
    dataset = None

    def __init__(self, cfg):
        self._cfg = cfg
        self._repository = self._cfg.get("general", "repository")
        
        self._check_structure()

    def _check_structure(self):
        if not os.path.exists(self._repository):
            os.mkdir(self._repository)
            os.mkdir(self._repository + "/day")
            os.mkdir(self._repository + "/week")
            os.mkdir(self._repository + "/month")

    def _gen_prev_dataset(self,  section,  path):
        if self.dataset - 1 == 0:
            prev_dataset = self._cfg.getint("general", self.mode + "_grace")
        else:
            prev_dataset = self.dataset - 1

        return "/".join([self._repository, self.mode,
                              str(prev_dataset), section, path.strip("\n")])

    def create_dirs(self, section, stdout):
        for item in stdout.readlines():
            prev_path = self._gen_prev_dataset(section,  item)
            cur_path = "/".join([self._repository, self.mode,
                              str(self.dataset), section, item.strip("\n")])

            if os.path.exists(prev_path):
                
                os.link(prev_path, cur_path)
            else:
                os.makedirs(cur_path)
