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