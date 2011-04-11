# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@ymail.com)
Project       Syncropy
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import psycopg2

class DBManager(object):
    _cfg = None

    def __init__(self, cfg):
        self._cfg = cfg

    def _check_schema(self, connection):
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(tablename) FROM pg_tables WHERE " +
                        "schemaname = 'public'")

        value = cursor.fetchone()[0]
        cursor.close()

        if value == 0:
            return False
        else:
            return True

    def _create_schema(self, connection):
        tables = [
                  "CREATE TABLE store (source VARCHAR(30), grace VARCHAR(5), dataset INTEGER, element VARCHAR(1024), element_type VARCHAR(2))",
                  "CREATE TABLE attributes (source VARCHAR(30), grace VARCHAR(5), dataset INTEGER, element VARCHAR(1024), element_user VARCHAR(50), element_group VARCHAR(50), element_type CHAR(2), element_perm VARCHAR(32), element_mtime INTEGER, element_ctime INTEGER)",
                  "CREATE TABLE status (grace VARCHAR(5), actual INTEGER, last_run TIMESTAMP)"
                 ]

        data = [
                "INSERT INTO status VALUES('hour', 0, current_timestamp)",
                "INSERT INTO status VALUES('day', 0, current_timestamp)",
                "INSERT INTO status VALUES('week', 0, current_timestamp)",
                "INSERT INTO status VALUES('month', 0, current_timestamp)"
               ]

        index = ["CREATE INDEX idx_attributes_1 ON attributes(source, grace, dataset)"]

        cursor = connection.cursor()

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
        connection = psycopg2.connect(host=self._cfg.get("database", "host"),
                                       database=self._cfg.get("database", "name"),
                                       user=self._cfg.get("database", "user"),
                                       password=self._cfg.get("database", "password"))
        
        if not self._check_schema(connection):
            self._create_schema(connection)

        return connection
