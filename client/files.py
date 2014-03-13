# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (client module)
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import hashlib
import json
import os
import stat
import subprocess

if os.name == "posix":
    import grp
    import pwd

class FileMode(object):
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

    def mode_to_octal(self):
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

    def _compute_nt_acl(self, path):
        result = {}
        # TODO: write code for managing ACLs in Windows environment
        return result

    def _compute_posix_acl(self, path):
        # FIXME: this is a quick&dirty code, replace with a native library if possible
        result = {}
        name = ""
        user = []
        group = []

        try:
            p = subprocess.Popen(["getfacl", path],
                                 shell=False,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            sts = p.wait()

            if sts == 0:
                for item in p.stdout.readlines():
                    line = item.decode("utf-8")
                    if line[:4] == "user" and line[4:6] != "::":
                        perms = {
                            "uid": line.split(":")[1],
                            "attrs": line.split(":")[2].strip("\n")
                        }
                        user.append(perms)
                    elif line[:5] == "group" and line[5:7] != "::":
                        perms = {
                            "gid": line.split(":")[1],
                            "attrs": line.split(":")[2].strip("\n")
                        }
                        group.append(perms)
                    """ Useless?
                    elif line[:6] == "# file":
                        name = "/" + line[8:].strip("\n")

                result["name"] = name
                """
                result["user"] = user
                result["group"] = group
            else:
                if p.stdout != None:
                    for item in p.stdout.readlines():
                        print("STDOUT: " + path + ": " + item.decode("utf-8"))

                if p.stderr != None:
                    for item in p.stderr.readlines():
                        print("STDERR: " + path + ": " + item.decode("utf-8"))
        except subprocess.CalledProcessError as e:
            # FIXME: manage the exception
            print(e)
            pass

        return result

    def _compute_nt_attrs(self, path):
        result = {}
        # TODO: write code for getting data from Windows systems
        return result

    def _compute_posix_attrs(self, path):
        result = {
            "type": None,
            "link": None,
            "size": None,
            "hash": None,
            "atime": None,
            "mtime": None,
            "ctime": None,
            "mode": None,
            "user": None,
            "group": None
        }

        attrs = FileMode(os.stat(path).st_mode)

        if os.path.isdir(path):
            result["type"] = "directory"
        elif os.path.islink(path):
            result["type"] = "symlink"
            result["link"] = os.readlink(path)
        else:
            result["type"] = "file"
            result["size"] = os.path.getsize(path)
            result["hash"] = self._hash(path)

        result["atime"] = int(os.path.getatime(path))
        result["mtime"] = int(os.path.getmtime(path))
        result["ctime"] = int(os.path.getctime(path))
        result["mode"] = attrs.mode_to_octal()
        result["user"] = pwd.getpwuid(os.stat(path).st_uid).pw_name
        result["group"] = grp.getgrgid(os.stat(path).st_gid).gr_name

        return result

    def _compute_metadata(self, path):
        result = {
            "name": path,
            "os": os.name
        }

        if os.name == "nt":
            result["attrs"] = self._compute_nt_attrs(path)
            if self.acl:
                result["acl"] = self._compute_nt_acl(path)
        else:
            result["attrs"] = self._compute_posix_attrs(path)
            if self.acl:
                result["acl"] = self._compute_posix_acl(path)

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
        for item in self._directory:
            for root, dirs, files in os.walk(item):
                for directory in dirs:
                    path = os.path.join(root, directory)
                    result = self._compute_metadata(path)
                    result["result"] = "ok"

                    yield json.dumps(result)

                for filename in files:
                    path = os.path.join(root, filename)
                    result = self._compute_metadata(path)
                    result["result"] = "ok"

                    yield json.dumps(result)
                result = self._compute_metadata(root)
                result["result"] = "ok"
                yield json.dumps(result)

class Send(object):
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
        with open(self._filename, "rb") as f:
            while True:
                data = f.read(2**20)
                if not data:
                    break
                yield data

class Receive(object):
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

    def data(self, socket):
        # TODO: write code for receive data
        pass

if __name__ == "__main__":
    pass
