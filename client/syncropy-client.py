#!/usr/bin/python

# -*- coding: utf-8 -*-
"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
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
    message = {}
    try:
        p = subprocess.Popen(cmd,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        sts = p.wait()

        if sts != 0:
            if p.stdout != None:
                message["result"] = "ko"
                for item in p.stdout.readlines():
                    string  = "\n".join([string, item])

                message["stdout"] = string
            if p.stderr != None:
                for item in p.stderr.readlines():
                    string  = "\n".join([string, item])

                message["stderr"] = string
        else:
            message["result"] = "ok"
            message["message"] = "Command successful"

        conn.send(json.dumps(message).encode("utf-8"))
    except subprocess.CalledProcessError as e:
        conn.send(json.dumps({"result": "ko", "error": str(e)}).encode("utf-8"))

def parse(command, conn):
    try:
        cmd = json.loads(command)
    except ValueError:
        conn.send(json.dumps({"result": "ko", "message": "Malformed command"}).encode("utf-8"))
        return True

    try:
        result = True
        if cmd["context"] == "file":
            if cmd["command"]["name"] == "list":
                try:
                    res = files.List()
                    res.directory = cmd["command"]["directory"]
                    res.acl = cmd["command"]["acl"]

                    for item in res.get():
                        conn.send(item.encode("utf-8"))
                except ValueError as ex:
                    conn.send(json.dumps({"result": "ko", "message": str(ex)}).encode("utf-8"))
            elif cmd["command"]["name"] == "get":
                res = files.Get()
                res.filename = cmd["command"]["filename"]

                conn.send(res.data())
            else:
                conn.send(json.dumps({"result": "ko", "message": "Command not found"}).encode("utf-8"))
        elif cmd["context"] == "system":
            if cmd["command"]["name"] == "exec":
                exec_command(cmd["command"]["value"], conn)
            elif cmd["command"]["name"] == "exit":
                result = False
        else:
            conn.send(json.dumps({"result": "ko", "message": "Context not found"}).encode("utf-8"))
    except KeyError:
        conn.send(json.dumps({"result": "ko", "message": "Malformed command"}).encode("utf-8"))

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
        try:
            execute = parse(data.decode("utf-8"), conn)
        except UnicodeDecodeError:
            pass
        conn.close()

    s.close()

def go(sysargs):
    args = init_args().parse_args(sysargs)

    if not args.port:
        print("Port not definied")
        sys.exit(1)
    else:
        serve(args.port)

if __name__ == "__main__":
    #import pycallgraph

    #pycallgraph.start_trace()
    go(sys.argv[1:])
    #pycallgraph.make_dot_graph('graph.png')

