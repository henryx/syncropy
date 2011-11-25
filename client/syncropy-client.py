#!/usr/bin/python

# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-client
Description   A backup system (client module)
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import argparse
import files
import json
import socket
import sys

def _init_args():
    args = argparse.ArgumentParser(description="Syncropy-client")
    args.add_argument("-p", "--port", metavar="<port>", help="Port wich listen")

    return args

def _parse(command, conn):

    try:
        cmd = json.loads(command)
    except ValueError:
        conn.send("Malformed command\n")
        return True

    if cmd["type"] == "file":
       if cmd["command"] == "list":
            res = files.List()
            res.directory = cmd["directory"]
            res.acl = cmd["acl"]

            conn.send(res.get())
            return True
    elif cmd["type"] == "system":
        if cmd["command"] == "exit":
            return False

def _serve(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', int(port)))

    s.listen(1)

    execute = True
    while execute:
        conn, addr = s.accept()
        data = conn.recv(1024)
        execute = _parse(data, conn)
        conn.close()

    s.close()

def go(sysargs):
    args = _init_args().parse_args(sysargs)

    if not args.port:
        print "Port not definied"
        sys.exit(1)
    else:
        _serve(args.port)

if __name__ == "__main__":
    go(sys.argv[1:])
