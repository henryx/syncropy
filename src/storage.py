# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

from datetime import datetime

import logging
import os, sys
import shutil
import src.db
import src.queries

class DbStorage(object):
    _cfg = None
    _con = None

    _dataset = None
    _mode = None
    _logger = None
    _section = None

    def __init__(self, cfg):
        self._cfg = cfg

        dbm = src.db.DBManager(self._cfg)
        self._logger = logging.getLogger("Syncropy")
        self._con = dbm.open()

    def __del__(self):
        if self._con:
            self._con.commit()
            self._con.close()

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = value

    @mode.deleter
    def mode(self):
        del self._mode

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, value):
        self._dataset = value
        
        if not self._mode:
            raise AttributeError, "Grace not definied"

    @dataset.deleter
    def dataset(self):
        del self._dataset

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        self._section = value

    @section.deleter
    def section(self):
        del self._section

    def check_dataset_exist(self):
        query = src.queries.Select()
        query.set_table("attrs")
        query.set_cols("count(*)")
        query.set_filter("grace = %s", self._mode)
        query.set_filter("dataset = %s", self._dataset, src.queries.SQL_AND)
        query.build()

        cur = self._con.cursor()
        cur.execute(query.get_statement(), query.get_values())

        result = cur.fetchone()[0]

        if result > 0:
            return True
        else:
            return False

    def remove_dataset(self):
        tables = ["attrs", "acls"]
        cur = self._con.cursor()
        
        for table in tables:
            delete = src.queries.Delete()
            delete.set_table(table)
            delete.filter("grace = %s", self._mode)
            delete.filter("dataset = %s", self._dataset, src.queries.SQL_AND)
            
            delete.build()
            cur.execute(delete.get_statement(), delete.get_values())

        self._con.commit()
        cur.close()

    def get_last_dataset(self):
        select = src.queries.Select()

        select.set_table("status")
        select.set_cols("actual")
        select.set_filter("grace = %s", self._mode)
        select.build()

        cur = self._con.cursor()
        cur.execute(select.get_statement(), select.get_values())

        dataset = cur.fetchone()[0]

        cur.close()
        return dataset

    def set_last_dataset(self, value):
        now = datetime.today()

        upd = src.queries.Update("%s")
        upd.set_table("status")
        upd.set_data(actual=value)
        upd.set_data(last_run=now.strftime("%Y-%m-%d %H:%M:%S"))
        upd.filter("grace = %s", self._mode)
        upd.build()

        cur = self._con.cursor()
        cur.execute(upd.get_statement(), upd.get_values())

        cur.close()

    def item_exist(self, item, attrs):
        cur_dataset = self.get_last_dataset()

        if cur_dataset == 0:
            cur_dataset = 1

        query = src.queries.Select()
        query.set_table("attrs")
        query.set_cols("count(*)")
        query.set_filter("grace = %s", self._mode)
        query.set_filter("source = %s", self._section, src.queries.SQL_AND)
        query.set_filter("dataset = %s", cur_dataset, src.queries.SQL_AND)
        query.set_filter("element = %s", item.decode("utf-8"), src.queries.SQL_AND)
        query.set_filter("element_mtime = %s", attrs["mtime"], src.queries.SQL_AND)
        query.set_filter("element_ctime = %s", attrs["ctime"], src.queries.SQL_AND)
        query.build()

        cur = self._con.cursor()
        cur.execute(query.get_statement(), query.get_values())

        res = cur.fetchone()[0]

        cur.close()

        if res > 0:
            return True
        else:
            return False

    def _add_element(self, element, attributes):
        ins = src.queries.Insert("%s")
        ins.set_table("attrs")
        ins.set_data(source=self._section,
                        dataset=self._dataset,
                        grace=self._mode,
                        element=element.decode("utf-8"),
                        element_user=attributes["user"],
                        element_group=attributes["group"],
                        element_ctime=attributes["ctime"],
                        element_mtime=attributes["mtime"])

        if attributes["type"] == "pl":
            ins.set_data(element_type="f")
        else:
            ins.set_data(element_type=attributes["type"])

        ins.build()
        try:
            cur = self._con.cursor()
            cur.execute(ins.get_statement(), ins.get_values())
            cur.close()
        except:
            # TODO: write code for better management
            print ins.get_statement()
            print ins.get_values()
            sys.exit(-1)

    def _add_acl(self, item, acl, idtype):
        ins = src.queries.Insert("%s")

        cur = self._con.cursor()
        ins.set_table("acls")
        ins.set_data(source=self._section,
                    dataset=self._dataset,
                    grace=self._mode,
                    element=item,
                    perms=acl["attrs"])
        
        if idtype == "u":
            ins.set_data(id=acl["uid"],
                    id_type=idtype)
        else:
            ins.set_data(id=acl["gid"],
                    id_type=idtype)

        ins.build()
        cur.execute(ins.get_statement(), ins.get_values())

        cur.close()

    def add(self, item, attrs=None, acls=None):
        if attrs:
            self._add_element(item, attrs)

        if acls:
            for user in acls["user"]: 
                self._add_acl(item, user, "u")

            for group in acls["group"]:
                self._add_acl(item, group, "g")

class FsStorage(object):
    _cfg = None
    _repository = None

    _dataset = None
    _logger = None
    _mode = None
    _section = None

    def __init__(self, cfg):
        super(FsStorage, self).__init__()
        self._cfg = cfg
        self._repository = self._cfg.get("general", "repository")

        self._logger = logging.getLogger("Syncropy")

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = value

    @mode.deleter
    def mode(self):
        del self._mode

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        self._section = value

    @section.deleter
    def section(self):
        del self._section

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, value):
        self._dataset = value

        if not self._mode:
            raise AttributeError, "Grace not definied"

    @dataset.deleter
    def dataset(self):
        del self._dataset

    def _dataset_path(self, previous):
        if previous:
            dataset = self._dataset - 1
        else:
            dataset = self._dataset

        if dataset == 0:
            dataset = self._cfg.getint("general", self._mode + "_grace")

        path = os.path.sep.join([self._repository, self._mode,
                        str(dataset), self._section])

        return path

    def check_dataset_exist(self):
        path = "/".join([self._repository, self._mode, str(self._dataset)])

        if os.path.exists(path):
            return True
        else:
            return False

    def remove_dataset(self):
        path = "/".join([self._repository, self._mode, str(self._dataset)])
        
        if os.path.exists(path):
            shutil.rmtree(path)

    def add(self, item, attrs, protocol):
        if attrs["type"] == "d":
            os.makedirs(self._dataset_path(False) + os.path.sep + item)
        elif attrs["type"] == "pl":
            os.link((self._dataset_path(True) + os.path.sep + item),
                    (self._dataset_path(False) + os.path.sep + item))
        elif attrs["type"] == "f":
            try:
                protocol.get_file(item, (self._dataset_path(False) + os.path.sep + item))
            except IOError as (errno, strerror):
                self._logger.error("I/O error({0}) for item {1}: {2}".format(errno, item, strerror))