# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
""" 

__author__ = "enrico"

import kinterbasdb

class DBManager(object):
    _cfg = None

    def __init__(self, cfg):
        self._cfg = cfg
        kinterbasdb.init(type_conv=200)

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
                  "CREATE TABLE store (source VARCHAR(30), grace VARCHAR(5), dataset INTEGER, element VARCHAR(1024), element_type CHAR(1))",
                  "CREATE TABLE attributes (source VARCHAR(30), grace VARCHAR(5), dataset INTEGER, element VARCHAR(1024), element_type CHAR(1), attr_type VARCHAR(3), attr_value VARCHAR(30))",
                  "CREATE TABLE status (grace VARCHAR(5), actual INTEGER, last_run TIMESTAMP)"
                 ]

        data = [
                "INSERT INTO status VALUES('hour', 0, current_timestamp)",
                "INSERT INTO status VALUES('day', 0, current_timestamp)",
                "INSERT INTO status VALUES('week', 0, current_timestamp)",
                "INSERT INTO status VALUES('month', 0, current_timestamp)"
               ]

        cursor = connection.cursor()

        for item in tables:
            cursor.execute(item)
        connection.commit()

        for item in data:
            cursor.execute(item)
        connection.commit()

        cursor.close()

    def open(self):
        connection = kinterbasdb.connect(host=self._cfg.get("database", "host"),
                                         database=self._cfg.get("database", "name"),
                                         user=self._cfg.get("database", "user"),
                                         password=self._cfg.get("database", "password"),
                                         charset="UTF8")
                                         
        
        connection.set_type_trans_in({
            "FIXED": kinterbasdb.typeconv_fixed_decimal.fixed_conv_in_precise
        })

        connection.set_type_trans_out({
            "FIXED": kinterbasdb.typeconv_fixed_decimal.fixed_conv_out_precise
        })
        
        if not self._check_schema(connection):
            self._create_schema(connection)

        return connection
