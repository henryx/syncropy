# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

import hashlib
import os

def check_structure(cfg):
    repository = cfg.get("general", "repository")

    if not os.path.exists(repository):
        os.mkdir(repository)

    if not os.path.exists(repository + "/day"):
        os.mkdir(repository + "/day")
        for day in range(cfg.getint("general", "daily_grace")):
            os.mkdir(repository + "/day/" + str(day+1))

    if not os.path.exists(repository + "/week"):
        os.mkdir(repository + "/week")
        for week in range(cfg.getint("general", "weekly_grace")):
            os.mkdir(repository + "/week/" + str(week+1))

    if not os.path.exists(repository + "/month"):
        os.mkdir(repository + "/month")
        for month in range(cfg.getint("general", "monthly_grace")):
            os.mkdir(repository + "/month/" + str(month+1))

def gethash(filename):
    return hashlib.md5(open(path, "rb").read()).hexdigest()