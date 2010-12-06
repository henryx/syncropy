#!/usr/bin/python2
# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

import ConfigParser
import os
import sys
import src.sync as sync

class Main(object):
    _cfgfile = None
    
    def __init__(self):
        pass

    def usage(self):
        sys.exit(0)
    
    def parseopt(self, opt):
        if opt.startswith("-c") or opt.startswith("--cfg="):
            if opt[1] == "-":
                self._cfgfile = opt[6:]
            else:
                self._cfgfile = opt[2:]
        
        elif option in ["-h", "--help"]:
            self.usage()

    def start(self):
        if not self._cfgfile:
            self._cfgfile = os.getcwd() + "/backupsync.cfg"
        
        cfg = ConfigParser.ConfigParser()
        cfg.readfp(open(self._cfgfile, "r"))
        
        s = sync.Sync(cfg)
        

if __name__ == "__main__":
    main = Main()
    
    for item in sys.argv[1:]:
        main.parseopt(item)
    main.start()
    