# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (server module)
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import json
import logging
import os
import shutil
from contextlib import closing

import fdb

class Database():
    _conn = None

    @property
    def connection(self):
        return self._conn

    def __init__(self, cfg):
        self._conn = fdb.connect(host=cfg["database"]["host"],
                                 port=cfg["database"]["port"],
                                 database=cfg["database"]["dbname"],
                                 user=cfg["database"]["user"],
                                 password=cfg["database"]["password"],
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

def fs_create_dir(cfg, section, dirname):
    path = os.sep.join([fs_compute_destination(cfg, section, False), dirname])
    os.makedirs(path)

def fs_save_file(cfg, section,filename, conn):
    logger = logging.getLogger("Syncropy")

    cmdget = {
        "context": "file",
        "command": {
            "name": "get",
            "filename": filename
        }
    }

    path = os.sep.join([fs_compute_destination(cfg, section, False), filename])
    conn.send(json.dumps(cmdget).encode("utf-8"))

    logger.debug(section["name"] + ": Transfer file " + filename)
    with open(path, "wb") as destfile:
        while True:
            data = conn.recv(2048)
            if not data:
                break
            destfile.write(data)

def fs_remove_dataset(cfg, section, previous=False):
    dataset = fs_compute_destination(cfg, section, previous)
    if os.path.exists(dataset):
        shutil.rmtree(dataset)

def fs_compute_destination(cfg, section, previous):
    if previous:
        if section["dataset"] == 1:
            dataset = int(cfg["dataset"][section["grace"]])
        else:
            dataset = section["dataset"] - 1
    else:
        dataset = section["dataset"]

    destination = os.sep.join([cfg["general"]["repository"],
                               section["grace"],
                               str(dataset),
                               section["name"]])
    return destination

def db_get_last_dataset(cfg, grace):

    with Database(cfg) as dbs:
        with closing(dbs.connection.cursor()) as cur:
            cur.execute("SELECT actual FROM status WHERE grace = ?", [grace])
            dataset = cur.fetchone()[0]

    return dataset

def db_set_last_dataset(cfg, grace, dataset):
    with Database(cfg) as dbm:
        with closing(dbm.connection.cursor()) as cursor:
            cursor.execute("UPDATE status SET actual = ?, last_run = CURRENT_TIMESTAMP WHERE grace = ?", [dataset, grace])

def db_del_dataset(dbm, section):
    with closing(dbm.connection.cursor()) as cursor:
        cursor.execute("DELETE FROM attrs WHERE area = ? AND grace = ? AND dataset = ?",
                       [section["name"], section["grace"], section["dataset"]])
        cursor.execute("DELETE FROM acls WHERE area = ? AND grace = ? AND dataset = ?",
                       [section["name"], section["grace"], section["dataset"]])

def db_save_attrs(dbm, section, data):
    # TODO: Add code for managing Windows systems

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

    with closing(dbm.connection.cursor()) as cursor:
        if data["os"] == "posix":
            save_posix_attrs()

def db_list_items(dbm, section, itemtype):
    with closing(dbm.connection.cursor()) as cursor:
        cursor.execute(" ".join(["SELECT element, os, hash, link, mtime,",
            "ctime FROM attrs WHERE type = ? AND area = ? AND grace = ? AND dataset = ?"]),
            [itemtype, section["name"], section["grace"], section["dataset"]])

        for item in cursor.fetchall():
            yield item

def db_item_exist(dbm, section, item, previous=None):
    if previous:
        dataset = previous
    else:
        dataset = section["dataset"]

    with closing(dbm.connection.cursor()) as cursor:
        cursor.execute(" ".join(["SELECT count(*) FROM attrs",
                                 "WHERE element = ? AND hash = ?",
                                 " AND area = ? AND grace = ? AND dataset = ?"]),
                       [item[0], item[2], section["name"], section["grace"], dataset])

        items = cursor.fetchone()

        if items[0] > 0:
            return True
        else:
            return False