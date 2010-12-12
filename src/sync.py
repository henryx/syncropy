# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

import os
import db
import protocols

class Sync(object):
    _cfg = None
    mode = None

    def __init__(self, cfg):
        self._cfg = cfg

    def _get_files(self, stdout):
        db = db.DBManager(self._cfg)

        con = db.open()
        for filename in stdout:
            # TODO: - Check into db if file exist
            #       - Download file
            #       - Retrieve file's metadata
            

    def execute(self):
        protocol = None

        sections = self._cfg.sections()

        sections.remove("general")
        for item in sections:
            paths = self._cfg.get(item, "path").split(",")

            if self._cfg.get(item, "type") == "ssh":
                protocol = protocols.SSH(self._cfg)
                for path in paths:
                    protocol.send_cmd("find " + path + " -type f")
                    self._get_files(protocol.get_stdout)
