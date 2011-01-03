# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

from datetime import datetime

import src.db
import src.protocols
import src.common
import src.queries

class Sync(object):
    _cfg = None
    _dbm = None
    _mode = None

    def __init__(self, cfg):
        self._cfg = cfg
        self._dbm = src.db.DBManager(self._cfg)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = value

    @mode.deleter
    def mode(self):
        del self._mode

    def _get_last_dataset(self):
        select = src.queries.Select()

        select.set_table("status")
        select.set_cols("actual")
        select.set_filter("grace = ?", self.mode)
        select.build()

        con = self._dbm.open()
        cur = con.cursor()
        cur.execute(select.get_statement(), select.get_values())

        dataset = cur.fetchone()[0]

        cur.close()
        con.close()
        return dataset

    def _set_last_dataset(self,  value):
        now = datetime.today()
        
        upd = src.queries.Update("?")
        upd.set_table("status")
        upd.set_data(actual=value)
        upd.set_data(last_run=now.strftime("%Y-%m-%d %H:%M:%S"))
        upd.filter("grace = ?", self._mode)
        upd.build()

        con = self._dbm.open()
        cur = con.cursor()
        cur.execute(upd.get_statement(), upd.get_values())
        
        con.commit()
        cur.close()
        con.close()

    def _get_dir_attrs(self, protocol):
        con = self._dbm.open()
        for item in protocol.get_stdout().readlines():
            print item.strip("\n")

    def _get_files(self, stdout):
        con = self._dbm.open()
        for filename in stdout:
            # TODO: - Check into db if file exist
            #       - Download file
            #       - Retrieve file's metadata
            pass

    def execute(self):
        protocol = None
        store = src.common.Storage(self._cfg)

        dataset = self._get_last_dataset()

        if dataset > self._cfg.getint("general", self.mode + "_grace"):
            dataset = 1
        else:
            dataset = dataset + 1

        sections = self._cfg.sections()
        sections.remove("general")
        sections.remove("database")

        for item in sections:
            paths = self._cfg.get(item, "path").split(",")

            if self._cfg.get(item, "type") == "ssh":
                protocol = src.protocols.SSH(self._cfg)
                protocol.connect(item)
                store.mode = self._mode
                store.section = item
                store.dataset = dataset
                for path in paths:
                    protocol.send_cmd("find " + path + " -type d")
                    store.create_dirs(protocol.get_stdout())
                    self._get_dir_attrs(protocol)
                    """
                    protocol.send_cmd("find " + path + " -type f")
                    self._get_files(protocol.get_stdout)
                    """

        self._set_last_dataset(dataset)
