# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (server module)
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

class Database(object):
    _cfg = None

    def __init__(self, cfg):
        self._cfg = cfg

class Filesystem(object):
    _cfg = None

    def __init__(self, cfg):
        self._cfg = cfg