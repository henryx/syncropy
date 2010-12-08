# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
""" 

from sqlite3 import dbapi2 as sqlite
import os

class DBManager(object):
    _cfg = None
    
    def __init__(self, cfg):
        self._cfg = cfg

        if not self._check_schema():
            self._create_schema()

    def _check_schema():
        con = sqlite.connect(cfg.get("general", "repository") + "/.store.sb")
        result = cursor.execute("select count(*) from sqlite_master")
        value = result.fetchone()[0]

        cursor.close()
        con.close()
        if value == 0:
            return False
        else:
            return True

    def _create_schema(self):
        pass