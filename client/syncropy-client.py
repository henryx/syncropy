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
import subprocess
import sys

def init_args():
    args = argparse.ArgumentParser(description="Syncropy-client")
    args.add_argument("-p", "--port", metavar="<port>", help="Port wich listen")

    return args

def exec_command(cmd, conn):
    try:
        p = subprocess.Popen(cmd,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        sts = p.wait()

        if sts != 0:
            if p.stdout != None:
                for item in p.stdout.readlines():
                    conn.send("STDOUT: " + item + "\n")

            if p.stderr != None:
                for item in p.stderr.readlines():
                    conn.send("STDERR: " + item + "\n")
        else:
            conn.send("Command successful\n")
    except subprocess.CalledProcessError as e:
        conn.send("Error: " + e +"\n")

def parse(command, conn):
    try:
        cmd = json.loads(command)
    except ValueError:
        conn.send("Malformed command\n")
        return True

    try:
        result = True
        if cmd["context"] == "file":
            if cmd["command"]["name"] == "list":
                res = files.List()
                res.directory = cmd["command"]["directory"]
                res.acl = cmd["command"]["acl"]

                conn.send(res.get())
            elif cmd["command"]["name"] == "get":
                res = files.Get()
                res.filename = cmd["command"]["filename"]

                conn.send(res.data())
            else:
                conn.send("Command not found\n")
        elif cmd["context"] == "system":
            if cmd["command"]["name"] == "exec":
                exec_command(cmd["command"]["value"], conn)
            elif cmd["command"]["name"] == "exit":
                result = False
        else:
            conn.send("Context not found\n")
    except KeyError:
        conn.send("Malformed command\n")

    return result

def serve(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', int(port)))

    s.listen(1)

    execute = True
    while execute:
        conn, addr = s.accept()
        data = conn.recv(1024)
        execute = parse(data, conn)
        conn.close()

    s.close()

def go(sysargs):
    args = init_args().parse_args(sysargs)

    if not args.port:
        print "Port not definied"
        sys.exit(1)
    else:
        serve(args.port)

if __name__ == "__main__":
    go(sys.argv[1:])
