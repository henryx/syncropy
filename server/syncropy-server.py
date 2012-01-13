#!/usr/bin/python

# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (server module)
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import argparse
import sys

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

def go(sysargs):
    args = init_args().parse_args(sysargs)

    if not args.cfg:
        print "configuration file not specified"
        sys.exit(1)

    if not args.mode:
        print "Backup mode not definied"
        sys.exit(2)

    if args.get_last_dataset:
        # TODO: write code for getting last dataset processed
        sys.exit(0)

    if not args.del_dataset:
        # TODO: Write code for remove a dataset
    else:
        # TODO: Write code for create a dataset

if __name__ == "__main__":
    go(sys.argv[1:])
