# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (client module)
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import hashlib
import json
import os
import stat

class Stat(object):
    SUID = 0
    SGID = 0
    STICKY = 0
    OWNER_READ = 0
    OWNER_WRITE = 0
    OWNER_EXECUTE = 0
    GROUP_READ = 0
    GROUP_WRITE = 0
    GROUP_EXECUTE = 0
    OTHER_READ = 0
    OTHER_WRITE = 0
    OTHER_EXECUTE = 0

    def __init__(self, mode=None):
        if mode & stat.S_ISUID:
            self.SUID = 4

        if mode & stat.S_ISGID:
            self.SGID = 2

        if mode & stat.S_ISVTX:
            self.STICKY = 1

        if mode & stat.S_IRUSR:
            self.OWNER_READ = 4

        if mode & stat.S_IWUSR:
            self.OWNER_WRITE = 2

        if mode & stat.S_IXUSR:
            self.OWNER_EXECUTE = 1

        if mode & stat.S_IRGRP:
            self.GROUP_READ = 4

        if mode & stat.S_IWGRP:
            self.GROUP_WRITE = 2

        if mode & stat.S_IXGRP:
            self.GROUP_EXECUTE = 1

        if mode & stat.S_IROTH:
            self.OTHER_READ = 4

        if mode & stat.S_IWOTH:
            self.OTHER_WRITE = 2

        if mode & stat.S_IXOTH:
            self.OTHER_EXECUTE = 1

    def to_octal(self):
        special = self.SUID + self.SGID + self.STICKY
        owner = self.OWNER_READ + self.OWNER_WRITE + self.OWNER_EXECUTE
        group = self.GROUP_READ + self.GROUP_WRITE + self.GROUP_EXECUTE
        other = self.OTHER_READ + self.OTHER_WRITE + self.OTHER_EXECUTE

        return str(special) + str(owner) + str(group) + str(other)

    def __str__(self):
        result = ""

        result += 'r' if self.OWNER_READ else '-'
        result += 'w' if self.OWNER_WRITE else '-'

        if self.SUID:
            result += 'S'
        elif self.OWNER_EXECUTE:
            result += 'x'
        else:
            result += '-'

        result += 'r' if self.GROUP_READ else '-'
        result += 'w' if self.GROUP_WRITE else '-'

        if self.SGID:
            result += 'S'
        elif self.GROUP_EXECUTE:
            result += 'x'
        else:
            result += '-'

        result += 'r' if self.OTHER_READ else '-'
        result += 'w' if self.OTHER_WRITE else '-'

        if self.STICKY:
            result += 'T'
        elif self.OTHER_EXECUTE:
            result += 'x'
        else:
            result += '-'

        return result

class List(object):
    _directory = None
    _acl = None

    def __init__(self):
        pass

    def _compute_acl_nt(self, path):
        result = {}
        # TODO: write code for managing ACLs in Windows environment
        return result

    def _compute_acl_posix(self, path):
        result = {}
        # TODO: write code for managing ACLs in Posix environment
        return result

    def _compute_attrs(self, path):
        result = {}
        attrs = Stat(os.stat(path).st_mode)

        if os.path.isdir(path):
            result["type"] = "directory"
        else:
            result["type"] = "file"
            result["size"] = os.path.getsize(path)
            result["hash"] = self._hash(path)

        result["atime"] = os.path.getatime(path)
        result["mtime"] = os.path.getmtime(path)
        result["ctime"] = os.path.getctime(path)
        result["mode"] = attrs.to_octal()

        return result

    def _compute_metadata(self, path):
        result = {}

        result["attrs"] = self._compute_attrs(path)

        if self._acl:
            if os.name == "nt":
                result["acl"] = self._compute_acl_nt(path)
            else:
                result["acl"] = self._compute_acl_posix(path)

        return result

    def _hash(self, path, block_size=2**20):
        md5 = hashlib.md5()

        f = open(path, "rb")
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, value):
        if type(value) != list:
            raise ValueError("Invalid directory list")

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
        result = {}

        for item in self._directory:
            for root, dirs, files in os.walk(item):
                for directory in dirs:
                    path = root + directory if root[-1:] == "/" else root + "/" + directory
                    result[path] = self._compute_metadata(path)

                for filename in files:
                    path = root + filename if root[-1:] == "/" else root + "/" + filename
                    result[path] = self._compute_metadata(path)

        return json.dumps([result])

class Get(object):
    _filename = None

    def __init__(self):
        pass

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value

    @filename.deleter
    def filename(self):
        del self._filename

    def data(self):
        f = open(self._filename, "rb")
        data = f.read()
        return data

if __name__ == "__main__":
    pass
