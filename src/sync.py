# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

import os

class Sync(object):
    _cfg = None
    day = None
    week = None
    month = None
    
    def __init__(self, cfg):
        self.day = False
        self.week = False
        self.month = False
        
        self._cfg = cfg
        self._check_structure()

    def _check_structure(self):
        repository = self._cfg.get("general", "repository")
        
        if not os.path.exists(repository):
            os.mkdir(repository)
        
        if not os.path.exists(repository + "/day"):
            os.mkdir(repository + "/day")
            for day in range(self._cfg.getint("general", "daily_grace")):
                os.mkdir(repository + "/day/" + str(day+1))

        if not os.path.exists(repository + "/week"):
            os.mkdir(repository + "/week")
            for week in range(self._cfg.getint("general", "weekly_grace")):
                os.mkdir(repository + "/week/" + str(week+1))

        if not os.path.exists(repository + "/month"):
            os.mkdir(repository + "/month")
            for month in range(self._cfg.getint("general", "monthly_grace")):
                os.mkdir(repository + "/month/" + str(month+1))