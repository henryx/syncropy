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

import os
import pickle
import shutil
from contextlib import closing

import fdb

class Common(object):
    _cfg = None
    _grace = None
    _dataset = None
    _section = None

    def __init__(self, cfg):
        self._cfg = pickle.loads(cfg)

    @property
    def grace(self):
        return self._grace

    @grace.setter
    def grace(self, value):
        self._grace = pickle.loads(value)

    @grace.deleter
    def grace(self):
        del self._grace

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, value):
        if not self._grace:
            raise AttributeError("Grace not defined")

        self._dataset = pickle.loads(value)

    @dataset.deleter
    def dataset(self):
        del self._dataset

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        if not self._dataset:
            raise AttributeError("Dataset not defined")

        self._section = pickle.loads(value)

    @section.deleter
    def section(self):
        del self._section

class Database():
    _conn = None

    @property
    def connection(self):
        return self._conn

    def __init__(self, cfg):
        self._conn = fdb.connect(host=cfg.get("database", "host"),
                                 port=cfg.get("database", "port"),
                                 database=cfg.get("database", "dbname"),
                                 user=cfg.get("database", "user"),
                                 password=cfg.get("database", "password"),
                                 charset="UTF8")

        if not self._check_schema():
            self._create_schema()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self._conn:
                self._conn.commit()
                self._conn.close()
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
            " ".join(["CREATE TABLE status (",
                      "grace VARCHAR(5),",
                      " actual INTEGER,",
                      " last_run TIMESTAMP)"]),
            " ".join(["CREATE TABLE attrs (",
                      "area VARCHAR(30),",
                      "grace VARCHAR(5),",
                      "dataset INTEGER,",
                      "element VARCHAR(1024),",
                      "os VARCHAR(32),",
                      "username VARCHAR(50),",
                      "groupname VARCHAR(50),",
                      "type VARCHAR(9),",
                      "link VARCHAR(1024),",
                      "hash VARCHAR(32),",
                      "perms VARCHAR(32),",
                      "mtime BIGINT,",
                      "ctime BIGINT,",
                      "compressed BOOLEAN)"]),
            " ".join(["CREATE TABLE acls (",
                      "area VARCHAR(30),",
                      "grace VARCHAR(5),",
                      "dataset INTEGER,",
                      "element VARCHAR(1024),",
                      "name VARCHAR(50),",
                      "type VARCHAR(5),",
                      "perms VARCHAR(3))"])
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

class Filesystem(Common):
    _logger = None
    _repository = None

    def __init__(self, cfg):
        super(Filesystem, self).__init__(cfg)

        self._repository = self._cfg.get("general", "repository")
        # FIXME: Pickle doesn't serialize the logger
        #self._logger = logging.getLogger("Syncropy")

    def _compute_destination(self, previous):
        if previous:
            if self.dataset == 1:
                dataset = self._cfg.getint("dataset", self._grace)
            else:
                dataset = self.dataset - 1
        else:
            dataset = self.dataset

        destination = os.sep.join([self._repository,
                                   self._grace,
                                   str(dataset),
                                   self._section])
        return destination

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        self._section = pickle.loads(value)

        destination = self._compute_destination(False)

        if not os.path.exists(destination):
            os.makedirs(destination)

    @section.deleter
    def section(self):
        del self._section

    def add(self, obj, objtype):
        if objtype == "directory":
            path = os.sep.join([self._compute_destination(False), obj])
            os.makedirs(path)
        elif objtype == "file":
            # TODO: write file to disk
            pass

    def remove(self, previous=False):
        shutil.rmtree(self._compute_destination(previous))

def db_get_last_dataset(cfg, grace):

    with Database(cfg) as dbs:
        cur = dbs.connection.cursor()

        cur.execute("SELECT actual FROM status WHERE grace = ?", [grace])
        dataset = cur.fetchone()[0]
        cur.close()

    return dataset

def db_del_dataset(dbm, section):
    cursor = dbm.connection.cursor()

    cursor.execute("DELETE FROM attrs WHERE area = ? AND grace = ? AND dataset = ?",
                   [section["name"], section["grace"], section["dataset"]])
    cursor.execute("DELETE FROM acls WHERE area = ? AND grace = ? AND dataset = ?",
                   [section["name"], section["grace"], section["dataset"]])
    cursor.close()

def db_save_attrs(dbm, section, data):
    # TODO: Add code for managing Windows systems

    cursor = dbm.connection.cursor()

    def save_posix_attrs():
        attrs = data["attrs"]

        cursor.execute(" ".join(["INSERT INTO attrs",
                    "(area, grace, dataset, element, os, username, groupname, type,",
                    "link, mtime, ctime, hash, perms, compressed)",
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"]),
                       [section["name"], section["grace"], section["dataset"], data["name"], data["os"],
                        attrs["user"], attrs["group"], attrs["type"], attrs["link"], attrs["mtime"], attrs["ctime"],
                        attrs["hash"], attrs["mode"], section["compressed"]])

        if "acl" in data:
            acls = data["acl"]

            for user in acls["user"]:
                cursor.execute(" ".join(["INSERT INTO acls",
                        "(area, grace, dataset, element, name, type, perms)",
                        "VALUES(?, ?, ?, ?, ?, ?, ?)"]),
                               [section["name"], section["grace"], section["dataset"], data["name"], user["uid"], "group", user["attrs"]])
            for group in acls["group"]:
                cursor.execute(" ".join(["INSERT INTO acls",
                        "(area, grace, dataset, element, name, type, perms)",
                        "VALUES(?, ?, ?, ?, ?, ?, ?)"]),
                               [section["name"], section["grace"], section["dataset"], data["name"], group["gid"], "group", group["attrs"]])

    if data["os"] == "posix":
        save_posix_attrs()

    cursor.close()

def db_list_items(dbm, section, itemtype):
    with closing(dbm.connection.cursor()) as cursor:
        cursor.execute(" ".join(["SELECT element, os, hash, link, mtime,",
            "ctime FROM attrs WHERE type = ? AND area = ? AND grace = ? AND dataset = ?"]),
            [itemtype, section["name"], section["grace"], section["dataset"]])

        for item in cursor.fetchall():
            yield (item,)