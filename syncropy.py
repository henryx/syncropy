#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import argparse
import ConfigParser
import logging.handlers
import os
import sys

import src.management

def init_args():
    args = argparse.ArgumentParser(description="Syncropy")
    args.add_argument("-c", "--cfg", metavar="<file>", type=file,
                      required=True, help="Use the specified configuration file")
    args.add_argument("-H", dest="mode", action='store_const',
                      const="hour", help="Hourly backup is executed")
    args.add_argument("-D", dest="mode", action='store_const',
                      const="day", help="Daily backup is executed")
    args.add_argument("-W", dest="mode", action='store_const',
                      const="week", help="Weekly backup is executed")
    args.add_argument("-M", dest="mode", action='store_const',
                      const="month", help="Monthly backup is executed")
    args.add_argument("-r", "--reload-dataset", action='store_const',
                      const=True, help="Reload a dataset")
    args.add_argument("--del-dataset", metavar="<dataset>",
                      help="Remove specified dataset")
    args.add_argument("--get-last-dataset", action='store_const',
                            const=True, help="Return last dataset processed")
    return args

def check_structure(repository):
    if not os.path.exists(repository):
        try:
            os.mkdir(repository)
            os.mkdir(repository + os.sep + "hour")
            os.mkdir(repository + os.sep + "day")
            os.mkdir(repository + os.sep + "week")
            os.mkdir(repository + os.sep + "month")
        except IOError as (errno, strerror):
            print "I/O error({0}): {1}".format(errno, strerror)
            sys.exit(1)

def set_log(filename, level):
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

def go(sysargs):
    args = init_args().parse_args(sysargs)

    if not args.mode:
        print "Backup mode not definied"

    cfg = ConfigParser.ConfigParser()
    cfg.readfp(args.cfg)

    check_structure(cfg.get("general", "repository"))
    set_log(filename=cfg.get("general", "log_file"),
            level=cfg.get("general", "log_level"))

    if args.get_last_dataset:
        s = src.management.Info(cfg)
        s.mode = args.mode

        print s.dataset
        sys.exit(0)

    if not args.del_dataset:
        s = src.management.Sync(cfg)
        s.dataset_reload = args.reload_dataset
    else:
        s = src.management.Remove(cfg)
        s.dataset = args.del_dataset

    s.mode = args.mode
    s.execute()

if __name__ == "__main__":
    #import pycallgraph

    #pycallgraph.start_trace()
    go(sys.argv[1:])
    #pycallgraph.make_dot_graph('graph.png')
