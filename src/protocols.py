# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       BackupSYNC
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import paramiko

class SSH(object):
    _cfg = None
    _client = None
    _stdin = None
    _stdout = None
    _stderr = None

    def __init__(self, cfg):
        self._cfg = cfg

    def connect(self, section):
        self._client = paramiko.SSHClient()
        self._client.load_system_host_keys()
        self._client.connect(
                             hostname=self._cfg.get(section, "remote_host"),
                             port=self._cfg.getint(section, "remote_port"),
                             username=self._cfg.get(section, "remote_user"),
                             password=self._cfg.get(section, "remote_password")
                            )

    def get_file(self, remote, local):
        sftp = self._client.open_sftp()
        sftp.get(remote, local)
        return sftp.stat(remote)

    def send_cmd(self, cmd):
        self._stdin, self._stdout, self._stderr = self._client.exec_command(cmd)

        error = 0
        errstr = []
        for value in self._stderr:
            error = error + 1
            errstr.append(value.strip("\n"))

        if error > 0:
            for value in errstr:
                print value

            return False
        else:
            return True

    def get_stdout(self):
        return self._stdout
