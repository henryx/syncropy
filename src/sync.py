# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import src.db
import src.protocols
import src.common
import src.queries

class Sync(object):
    _cfg = None
    _dbm = None
    mode = None

    def __init__(self, cfg):
        self._cfg = cfg
        self._dbm = src.db.DBManager(self._cfg)

    def _get_last_dataset(self):
        select = src.queries.Select("?")

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
        ins = src.queries.Update("?")

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

        store.mode = self.mode
        store.dataset = dataset

        sections = self._cfg.sections()
        sections.remove("general")
        sections.remove("database")

        for item in sections:
            paths = self._cfg.get(item, "path").split(",")

            if self._cfg.get(item, "type") == "ssh":
                protocol = src.protocols.SSH(self._cfg)
                protocol.connect(item)
                for path in paths:
                    protocol.send_cmd("find " + path + " -type d")
                    store.create_dirs(item, protocol.get_stdout())
                    """
                    protocol.send_cmd("find " + path + " -type f")
                    self._get_files(protocol.get_stdout)
                    """

        self._set_last_dataset(dataset)
