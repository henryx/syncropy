#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import ConfigParser
import logging
import os
import sys
import src.sync

class Main(object):
    _cfgfile = None
    _mode = None

    def __init__(self):
        pass

    def _set_log(self, filename, level):
        LEVELS = {'debug': logging.DEBUG,
                  'info': logging.INFO,
                  'warning': logging.WARNING,
                  'error': logging.ERROR,
                  'critical': logging.CRITICAL
                 }
          
        logger = logging.getLogger("BackupSYNC")
        logger.setLevel(LEVELS.get(level, logging.NOTSET)

        handler = logging.handlers.RotatingFileHandler(
              filename, maxBytes=20480, backupCount=20)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
        

    def usage(self, exit_mode):
        print "Usage:"
        print "-c<file> or --cfg=<file> Use the specified configuration file"
        print "-h                       Hourly backup is executed"
        print "-d                       Daily backup is executed"
        print "-w                       Weekly backup is executed"
        print "-m                       Monthly backup is executed"

        sys.exit(exit_mode)

    def parseopt(self, opt):
        if opt.startswith("-c") or opt.startswith("--cfg="):
            if opt[1] == "-":
                self._cfgfile = opt[6:]
            else:
                self._cfgfile = opt[2:]
        elif opt in ["-h"]:
            self._mode = "hour"
        elif opt in ["-d"]:
            self._mode = "day"
        elif opt in ["-m"]:
            self._mode = "month"
        elif opt in ["w"]:
            self._mode = "week"
        elif opt in ["-?", "--help"]:
            self.usage(0)

    def start(self):
        if not self._cfgfile:
            print "Configuration file not found"
            self.usage(1)

        if not self._mode:
            print "Backup mode not definied"
            self.usage(1)

        

        cfg = ConfigParser.ConfigParser()
        cfg.readfp(open(self._cfgfile, "r"))

        self._set_log(filename=self._cfgfile.get("general", "log_file"),
                      level=self._cfgfile.get("general", "log_level"))

        s = src.sync.Sync(cfg)
        s.mode = self._mode
        s.execute()

if __name__ == "__main__":
    #import pycallgraph

    #pycallgraph.start_trace()
    main = Main()

    for item in sys.argv[1:]:
        main.parseopt(item)
    main.start()
    #pycallgraph.make_dot_graph('backupsync.png')
