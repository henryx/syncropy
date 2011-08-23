#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import ConfigParser
import logging.handlers
import os
import sys

import src.management

class Main(object):
    _cfgfile = None
    _mode = None
    _reload = None
    _remove_data = None
    _get_last = None

    def __init__(self):
        self._mode = ""
        self._reload = False
        self._get_last_dataset = False
        self._remove_data = -1

    def usage(self, exit_mode):
        print "Usage:"
        print "-c<file> or --cfg=<file> Use the specified configuration file"
        print "-h                       Hourly backup is executed"
        print "-d                       Daily backup is executed"
        print "-w                       Weekly backup is executed"
        print "-m                       Monthly backup is executed"
        print "-r                       Reload a dataset"
        print "--del-dataset=<dataset>  Remove specified dataset"
        print "--get-last-dataset       Return last dataset processed"

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
        elif opt in ["-w"]:
            self._mode = "week"
        elif opt in ["-r"]:
            self._reload = True
        elif opt.startswith("--del-dataset="):
            self._remove_data = opt[14:]
        elif opt == "--get-last-dataset":
            self._get_last_dataset = True
        elif opt in ["-?", "--help"]:
            self.usage(0)

    def _check_structure(self, repository):
        if not os.path.exists(repository):
            try:
                os.mkdir(repository)
                os.mkdir(repository + "/hour")
                os.mkdir(repository + "/day")
                os.mkdir(repository + "/week")
                os.mkdir(repository + "/month")
            except IOError as (errno, strerror):
                print "I/O error({0}): {1}".format(errno, strerror)
                sys.exit(1)

    def _set_log(self, filename, level):
        LEVELS = {'debug': logging.DEBUG,
                  'info': logging.INFO,
                  'warning': logging.WARNING,
                  'error': logging.ERROR,
                  'critical': logging.CRITICAL
                 }

        logger = logging.getLogger("Syncropy")
        logger.setLevel(LEVELS.get(level.lower(), logging.NOTSET))

        handler = logging.handlers.RotatingFileHandler(
                filename, maxBytes=20971520, backupCount=20)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)

    def start(self):
        if not self._cfgfile:
            print "Configuration file not found"
            self.usage(1)

        if not self._mode:
            print "Backup mode not definied"
            self.usage(1)

        cfg = ConfigParser.ConfigParser()
        cfg.readfp(open(self._cfgfile, "r"))

        self._check_structure(cfg.get("general", "repository"))

        self._set_log(filename=cfg.get("general", "log_file"),
                      level=cfg.get("general", "log_level"))

        if self._get_last_dataset:
            s = src.management.Info(cfg)
            s.mode = self._mode
            
            print s.dataset
            sys.exit(0)

        if self._remove_data == -1:
            s = src.management.Sync(cfg)
            s.dataset_reload = self._reload
        else:
            s = src.management.Remove(cfg)
            s.dataset = self._remove_data

        s.mode = self._mode
        s.execute()

if __name__ == "__main__":
    #import pycallgraph

    #pycallgraph.start_trace()
    main = Main()

    for item in sys.argv[1:]:
        main.parseopt(item)
    main.start()
    #pycallgraph.make_dot_graph('graph.png')
