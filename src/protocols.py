# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy
Description   A backup system
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import logging
import paramiko

class SSH(object):
    _cfg = None
    _client = None
    _errstr = None
    _logger = None
    _stdin = None
    _stdout = None
    _stderr = None
    _sftp = None

    def __init__(self, cfg):
        self._cfg = cfg
        self._logger = logging.getLogger("Syncropy")

    def connect(self, section):
        self._client = paramiko.SSHClient()
        self._client.load_system_host_keys()
        self._client.connect(
                             hostname=self._cfg.get(section, "remote_host"),
                             port=self._cfg.getint(section, "remote_port"),
                             username=self._cfg.get(section, "remote_user"),
                             password=self._cfg.get(section, "remote_password")
                            )
        self._sftp = self._client.open_sftp()

    def stat_file(self, remote):
        return self._sftp.stat(remote)

    def get_file(self, remote, local):
        self._sftp.get(remote, local)

    def send_cmd(self, cmd):
        self._stdin, self._stdout, self._stderr = self._client.exec_command(cmd)

    def get_stdout(self):
        return self._stdout
    
    def get_errstr(self):
        return self._errstr
    
    def is_err_cmd(self):
        error = 0
        self._errstr = []
        for value in self._stderr:
            error = error + 1
            if value.strip("\n") != "":
                self._errstr.append(value.strip("\n"))

        if error > 0:
            return True
        else:
            return False

    def close(self):
        self._client.close()
