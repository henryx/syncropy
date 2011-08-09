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
import sys
import src.sync

class Main(object):
    _cfgfile = None
    _mode = None
    _reload = None

    def __init__(self):
        self._mode = ""
        self._reload = False

    def usage(self, exit_mode):
        print "Usage:"
        print "-c<file> or --cfg=<file> Use the specified configuration file"
        print "-h                       Hourly backup is executed"
        print "-d                       Daily backup is executed"
        print "-w                       Weekly backup is executed"
        print "-m                       Monthly backup is executed"
        print "-r                       Reload a dataset"

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

        s = src.sync.Sync(cfg)
        s.mode = self._mode
        s.dataset_reload = self._reload
        s.execute()

if __name__ == "__main__":
    #import pycallgraph

    #pycallgraph.start_trace()
    main = Main()

    for item in sys.argv[1:]:
        main.parseopt(item)
    main.start()
    #pycallgraph.make_dot_graph('graph.png')
