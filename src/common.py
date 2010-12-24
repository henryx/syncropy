# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

import os
import src.db
import src.queries

class Storage(object):
    _cfg = None
    mode = None
    dataset = None

    def __init__(self, cfg):
        self._cfg = cfg
        self._check_structure()

    def _check_structure(self):
        repository = self._cfg.get("general", "repository")

        if not os.path.exists(repository):
            os.mkdir(repository)
            os.mkdir(repository + "/day")
            os.mkdir(repository + "/week")
            os.mkdir(repository + "/month")

    def create_dirs(self, section, stdout):
        repository = self._cfg.get("general", "repository")
        for item in stdout.readlines():
            prev_path = "/".join([repository, self.mode,
                              str(self.dataset -1), section, item.strip("\n")])
            cur_path = "/".join([repository, self.mode,
                              str(self.dataset), section, item.strip("\n")])
            print prev_path
            print cur_path
            if os.path.exists(prev_path):
                os.link(prev_path, cur_path)
            else:
                os.makedirs(cur_path)