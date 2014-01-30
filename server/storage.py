# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (server module)
License       GPL version 2 (see GPL.txt for details)
"""

"""
NOTE:

Grace:
    Hourly backup;
    Daily backup;
    Weekly backup;
    Monthly backup

Dataset:
    An incremental for grace backup

Section:
    A machine that backup

"""

__author__ = "enrico"

import logging
import os
import fdb

class Common(object):
    _cfg = None
    _grace = None
    _dataset = None
    _section = None

    def __init__(self, cfg):
        self._cfg = cfg

    @property
    def grace(self):
        return self._grace

    @grace.setter
    def grace(self, value):
        self._grace = value

    @grace.deleter
    def grace(self):
        del self._grace

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, value):
        if not self._grace:
            raise AttributeError("Grace not definied")

        self._dataset = value

    @dataset.deleter
    def dataset(self):
        del self._dataset

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        if not self._dataset:
            raise AttributeError("Dataset not definied")

        self._section = value

    @section.deleter
    def section(self):
        del self._section

class Database(Common):
    _conn = None

    def __init__(self, cfg):
        super(Database, self).__init__(cfg)

        self._conn = fdb.connect(host=self._cfg.get("database", "host"),
                                 port=self._cfg.get("database", "port"),
                                 database=self._cfg.get("database", "dbname"),
                                 user=self._cfg.get("database", "user"),
                                 password=self._cfg.get("database", "password"),
                                 charset="UTF8")

        if not self._check_schema():
            self._create_schema()

    def __del__(self):
        try:
            if self._con:
                self._con.commit()
                self._con.close()
        except:
            pass

    def _check_schema(self):
        cursor = self._conn.cursor()
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

    def _create_schema(self):
        domains = ["CREATE DOMAIN BOOLEAN AS SMALLINT CHECK (value is null or value in (0, 1))"]

        index = [
            "CREATE INDEX idx_attrs_1 ON attrs(area, grace, dataset)",
            "CREATE INDEX idx_attrs_2 ON attrs(area, grace, dataset, hash)",
            "CREATE INDEX idx_attrs_3 ON attrs(area, grace, dataset, type)",
            "CREATE INDEX idx_acls_1 ON acls(area, grace, dataset)"
        ]

        tables = [
            "CREATE TABLE status ("
            + "grace VARCHAR(5),"
            + " actual INTEGER,"
            + " last_run TIMESTAMP)",
            "CREATE TABLE attrs ("
            + "area VARCHAR(30),"
            + " grace VARCHAR(5),"
            + " dataset INTEGER,"
            + " element VARCHAR(1024),"
            + " os VARCHAR(32),"
            + " username VARCHAR(50),"
            + " groupname VARCHAR(50),"
            + " type VARCHAR(9),"
            + " link VARCHAR(1024),"
            + " hash VARCHAR(32),"
            + " perms VARCHAR(32),"
            + " mtime BIGINT,"
            + " ctime BIGINT,"
            + "compressed BOOLEAN)",
            "CREATE TABLE acls ("
            + "area VARCHAR(30),"
            + " grace VARCHAR(5),"
            + " dataset INTEGER,"
            + " element VARCHAR(1024),"
            + " name VARCHAR(50),"
            + " type VARCHAR(5),"
            + " perms VARCHAR(3))"
        ]

        data = [
            "INSERT INTO status VALUES('hour', 0, CURRENT_TIMESTAMP)",
            "INSERT INTO status VALUES('day', 0, CURRENT_TIMESTAMP)",
            "INSERT INTO status VALUES('week', 0, CURRENT_TIMESTAMP)",
            "INSERT INTO status VALUES('month', 0, CURRENT_TIMESTAMP)"
        ]

        cursor = self._conn.cursor()

        for item in domains:
            cursor.execute(item)
        self._conn.commit()

        for item in tables:
            cursor.execute(item)
        self._conn.commit()

        for item in index:
            cursor.execute(item)
        self._conn.commit()

        for item in data:
            cursor.execute(item)
        self._conn.commit()

        cursor.close()

    def get_last_dataset(self):
        cur = self._conn.cursor()

        cur.execute("SELECT actual FROM status WHERE grace = ?", [self._grace])
        dataset = cur.fetchone()[0]
        cur.close()

        return dataset

    def add(self):
        pass

class Filesystem(Common):
    _logger = None
    _repository = None

    def __init__(self, cfg):
        super(Filesystem, self).__init__(cfg)

        self._repository = self._cfg.get("general", "repository")
        self._logger = logging.getLogger("Syncropy")

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        self._section = value

        if not os.path.exists(os.sep.join([self._cfg.get("general", "repository"),
                                           self._grace,
                                           str(self._dataset),
                                           self._section])):
            os.makedirs(os.sep.join([self._cfg.get("general", "repository"),
                                     self._grace,
                                     str(self._dataset),
                                     self._section]))

    @section.deleter
    def section(self):
        del self._section

    def add(self):
        pass
