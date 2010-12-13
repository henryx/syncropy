# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

import os
import src.db
import src.protocols
import src.common
import src.queries

class Sync(object):
    _cfg = None
    mode = None

    def __init__(self, cfg):
        self._cfg = cfg

    def _last_dataset(self):
        dbm = src.db.DBManager(self._cfg)
        select = src.queries.Select("?")

        select.set_table("status")
        select.set_cols("actual")
        select.set_filter("grace = ?", self.mode)
        select.build()

        con = dbm.open()
        cur = con.cursor()
        cur.execute(select.get_statement(), select.get_values())

        dataset = cur.fetchone()[0]

        cur.close()
        con.close()
        return dataset

    def _get_files(self, stdout):
        db = db.DBManager(self._cfg)

        con = db.open()
        for filename in stdout:
            # TODO: - Check into db if file exist
            #       - Download file
            #       - Retrieve file's metadata
            pass

    def execute(self):
        protocol = None
        store = src.common.Storage(self._cfg)

        dataset = self._last_dataset()

        if dataset == self._cfg.getint("general", self.mode + "_grace"):
            dataset = 0
        else:
            dataset = dataset + 1

        store.mode = self.mode
        store.dataset = dataset

        sections = self._cfg.sections()

        sections.remove("general")
        for item in sections:
            paths = self._cfg.get(item, "path").split(",")

            if self._cfg.get(item, "type") == "ssh":
                protocol = src.protocols.SSH(self._cfg)
                protocol.connect(item)
                for path in paths:
                    protocol.send_cmd("find " + path + " -type d")
                    store.create_dirs(protocol.get_stdout())
                    """
                    protocol.send_cmd("find " + path + " -type f")
                    self._get_files(protocol.get_stdout)
                    """