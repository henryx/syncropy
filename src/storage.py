# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

from datetime import datetime

import os
import shutil
import src.db
import src.queries

class DbStorage(object):
    _cfg = None
    _con = None

    _mode = None
    _dataset = None
    _section = None

    def __init__(self, cfg):
        self._cfg = cfg
        
        dbm = src.db.DBManager(self._cfg)
        self._con = dbm.open()
        
    def __del__(self):
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
        
        if not self._section:
            raise AttributeError, "Section not definied"
        
        if not self._mode:
            raise AttributeError, "Grace not definied"        

        if self._check_dataset_exist():
            self._del_dataset()

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

    def _check_dataset_exist(self):
        query = src.queries.Select()
        query.set_table("store")
        query.set_cols("count(*)")
        query.set_filter("grace = ?", self._mode)
        query.set_filter("source = ?", self._section, src.queries.SQL_AND)
        query.set_filter("dataset = ?", self._dataset, src.queries.SQL_AND)
        query.build()
        
        cur = self._con.cursor()
        cur.execute(query.get_statement(), query.get_values())
        
        result = cur.fetchone()[0]
        
        if result > 0:
            return True
        else:
            return False

    def _del_dataset(self):
        # NOTE: for convenience, these statements has written in direct form
        delete = [
            "DELETE FROM store WHERE source = ? AND grace = ? AND dataset = ?",
            "DELETE FROM attributes WHERE source = ? AND grace = ? AND dataset = ?",
        ]
        
        cur = self._con.cursor()
        
        for item in delete:
            cur.execute(item, (self._section, self._mode, self._dataset))

        self._con.commit()
        cur.close()

    def get_last_dataset(self):
        select = src.queries.Select()

        select.set_table("status")
        select.set_cols("actual")
        select.set_filter("grace = ?", self._mode)
        select.build()

        cur = self._con.cursor()
        cur.execute(select.get_statement(), select.get_values())

        dataset = cur.fetchone()[0]

        cur.close()
        return dataset

    def set_last_dataset(self, value):
        now = datetime.today()

        upd = src.queries.Update("?")
        upd.set_table("status")
        upd.set_data(actual=value)
        upd.set_data(last_run=now.strftime("%Y-%m-%d %H:%M:%S"))
        upd.filter("grace = ?", self._mode)
        upd.build()

        cur = self._con.cursor()
        cur.execute(upd.get_statement(), upd.get_values())
        
        self._con.commit()
        cur.close()

    def add_dir(self, directory):
        ins = src.queries.Insert("?")
        ins.set_table("store")
        ins.set_data(source=self._section, dataset=self._dataset,
                     grace=self._mode, element=directory, element_type="d")
        ins.build()
        
        cur = self._con.cursor()
        cur.execute(ins.get_statement(), ins.get_values())
        
        self._con.commit()
        cur.close()

class FsStorage(object):
    _cfg = None
    _repository = None
    
    _mode = None
    _dataset = None
    _section = None

    def __init__(self, cfg):
        super(FsStorage, self).__init__()
        self._cfg = cfg
        self._repository = self._cfg.get("general", "repository")
        
        self._check_structure()

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
        
        if not self._section:
            raise AttributeError, "Section not definied"
        
        if not self._mode:
            raise AttributeError, "Grace not definied"
        
        path = "/".join([self._repository, self._mode, str(self._dataset), self._section])

        if os.path.exists(path):
            self._remove_dataset(path, self._dataset)

    @dataset.deleter    
    def dataset(self):
        del self._dataset

    def _remove_dataset(self, path, dataset):
        shutil.rmtree(path)
        # TODO: remove dataset from database

    def _check_structure(self):
        if not os.path.exists(self._repository):
            os.mkdir(self._repository)
            os.mkdir(self._repository + "/hour")
            os.mkdir(self._repository + "/day")
            os.mkdir(self._repository + "/week")
            os.mkdir(self._repository + "/month")

    def _gen_prev_dataset(self, path):
        if self.dataset - 1 == 0:
            prev_dataset = self._cfg.getint("general", self._mode + "_grace")
        else:
            prev_dataset = self.dataset - 1

        return "/".join([self._repository, self._mode,
                         str(prev_dataset), self._section, path.strip("\n")])

    def add_dir(self, directory):
        path = "/".join([self._repository, self._mode,
                        str(self.dataset), self._section, directory.strip("\n")])
        os.makedirs(path)