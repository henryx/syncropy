# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (server module)
License       GPL version 2 (see GPL.txt for details)
"""

"""
NOTE:

Grace:
    Hourly backup;
    Daily backup;
    Weekly backup;
    Monthly backup

Dataset:
    An incremental for grace backup

Section:
    A machine that backup

"""

__author__ = "enrico"

class Common(object):
    _cfg = None
    _section = None
    _dbstore = None
    _filestore = None

    def __init__(self, cfg):
        self._cfg = cfg

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        self._section = section

    @section.deleter
    def section(self):
        del self._section

    @property
    def filestore(self):
        return self._filestore

    @filestore.setter
    def filestore(self, value):
        self._filestore = value

    @filestore.deleter
    def filestore(self):
        del self._filestore

    @property
    def dbstore(self):
        return self._dbstore

    @dbstore.setter
    def dbstore(self, value):
        self._dbstore = value

    @dbstore.deleter
    def dbstore(self):
        del self._dbstore

class FileSync(Common)
    def __init__(self, cfg):
        super(FileSync, self).__init__(cfg)
        