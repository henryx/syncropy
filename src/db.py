# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
""" 

import kinterbasdb
import os

class DBManager(object):
    _cfg = None

    def __init__(self, cfg):
        self._cfg = cfg

    def _check_schema(self, connection):
        cursor = connection.cursor()
        cursor.execute(" ".join(["SELECT COUNT(rdb$relation_name)",
                                 "FROM rdb$relations WHERE",
                                 "rdb$relation_name NOT LIKE 'RDB$%'",
                                 "AND rdb$relation_name NOT LIKE 'MON$%'"]))
        value = cursor.fetchone()[0]

        cursor.close()

        if value == 0:
            return False
        else:
            return True

    def _create_schema(self, connection):
        tables = [
                  "CREATE TABLE files (source VARCHAR(30), hash VARCHAR(32))",
                  "CREATE TABLE original_path (hash VARCHAR(32), location VARCHAR(1024))",
                  "CREATE TABLE repo_path(hash VARCHAR(32), location VARCHAR(1024))",
                  "CREATE TABLE attributes (hash VARCHAR(32), attr_type VARCHAR(3), attr_value VARCHAR(30))",
                  "CREATE TABLE status (grace VARCHAR(5), actual INTEGER)"
                 ]

        data = [
                "INSERT INTO status VALUES('day', 0)",
                "INSERT INTO status VALUES('week', 0)",
                "INSERT INTO status VALUES('month', 0)"
               ]

        cursor = connection.cursor()

        for item in tables:
            cursor.execute(item)
        connection.commit()

        for item in data:
            cursor.execute(item)

        cursor.close()

        connection.commit()

    def open(self):
        connection = kinterbasdb.connect(host=self._cfg.get("database", "host"),
                                         database=self._cfg.get("database", "name"),
                                         user=self._cfg.get("database", "user"),
                                         password=self._cfg.get("database", "password"),
                                         charset="UTF8")

        if not self._check_schema(connection):
            self._create_schema(connection)

        return connection