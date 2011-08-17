# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

from sqlite3 import dbapi2 as sqlite

class DBManager(object):
    _cfg = None

    def __init__(self, cfg):
        self._cfg = cfg

    def _check_schema(self, connection):
        cursor = connection.cursor()
        cursor.execute("select count(*) from sqlite_master")

        value = cursor.fetchone()[0]
        cursor.close()

        if value == 0:
            return False
        else:
            return True

    def _create_schema(self, connection):
        pragmas = [
                   "PRAGMA synchronous=OFF",
                   "PRAGMA journal_mode=WAL"
                  ]
        
        tables = [
                  "CREATE TABLE attrs (source VARCHAR(30), grace VARCHAR(5), dataset INTEGER, element VARCHAR(1024), element_user VARCHAR(50), element_group VARCHAR(50), element_type CHAR(1), element_perm VARCHAR(32), element_mtime INTEGER, element_ctime INTEGER)",
                  "CREATE TABLE acls (source VARCHAR(30), grace VARCHAR(5), dataset INTEGER, element VARCHAR(1024), id VARCHAR(50), id_type VARCHAR(1), perms VARCHAR(3))", 
                  "CREATE TABLE status (grace VARCHAR(5), actual INTEGER, last_run TIMESTAMP)"
                 ]

        data = [
                "INSERT INTO status VALUES('hour', 0, current_timestamp)",
                "INSERT INTO status VALUES('day', 0, current_timestamp)",
                "INSERT INTO status VALUES('week', 0, current_timestamp)",
                "INSERT INTO status VALUES('month', 0, current_timestamp)"
               ]

        index = [
                 "CREATE INDEX idx_store_1 ON attrs(grace, source, dataset)",
                 "CREATE INDEX idx_store_2 ON attrs(grace, source, dataset, element, element_mtime, element_ctime)"
                ]

        cursor = connection.cursor()

        for item in pragmas:
            cursor.execute(item)
        connection.commit()

        for item in tables:
            cursor.execute(item)
        connection.commit()

        for item in data:
            cursor.execute(item)
        connection.commit()

        for item in index:
            cursor.execute(item)
        connection.commit()

        cursor.close()

    def open(self):
        db = self._cfg.get("general", "repository") + "/.store.db"
        connection = sqlite.connect(db)

        if not self._check_schema(connection):
            self._create_schema(connection)

        return connection
