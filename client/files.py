# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-client
Description   A backup system (client module)
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

class List(object):
    _directory = None
    _acl = None

    def __init__(self):
        pass

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, value):
        self._directory = value

    @directory.deleter
    def directory(self):
        del self._directory

    @property
    def acl(self):
        return self._acl

    @acl.setter
    def acl(self, value):
        self._acl = value

    @acl.deleter
    def acl(self):
        del self._acl

    def get(self):
        return "All files are processed\n"
    