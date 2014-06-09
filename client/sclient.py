# !/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Copyright (C) 2012 Enrico Bianchi (enrico.bianchi@gmail.com)
Project       Syncropy-ng
Description   A backup system (client module)
License       GPL version 2 (see GPL.txt for details)
"""

__author__ = "enrico"

import argparse
import configparser
import files
import json
import logging
import socket
import ssl
import subprocess
import sys

def init_args():
    args = argparse.ArgumentParser(description="Syncropy-client")
    args.add_argument("-p", "--port", required=True, metavar="<port>", help="Port which listen")
    args.add_argument("-l", "--listen", metavar="<address>", help="Address to listen")
    args.add_argument("-S", "--ssl", metavar="<file>", help="Enable SSL support")

    return args

def get_socket(port, address=None, sslparams=None):
    if sslparams["enabled"]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.load_cert_chain(certfile=sslparams["pem"],
                                password=sslparams["password"])

        context.load_verify_locations(cafile=sslparams["pem"])
        context.verify_mode = ssl.CERT_REQUIRED
        s = context.wrap_socket(sock, server_side=True)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    if address:
        s.bind((address, int(port)))
    else:
        s.bind(('', int(port)))

    return s

def exec_command(cmd):
    message = {}
    string = ""

    try:
        p = subprocess.Popen(cmd,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        sts = p.wait()

        if sts != 0:
            message["result"] = "ko"
            if p.stdout != None:
                message["type"] = "stdout"
                for item in p.stdout.readlines():
                    string = "\n".join([string, item.decode("utf-8")])

                message["message"] = string
            if p.stderr != None:
                message["type"] = "stderr"
                for item in p.stderr.readlines():
                    string = "\n".join([string, item.decode("utf-8")])

                message["message"] = string
        else:
            message["result"] = "ok"
            message["message"] = "Command successful"

        return (json.dumps(message) + "\n").encode("utf-8")
    except subprocess.CalledProcessError as e:
        return (json.dumps({"result": "ko", "error": str(e)}) + "\n").encode("utf-8")

def parse(command, conn):
    try:
        cmd = json.loads(command.decode('utf-8'))
    except ValueError:
        conn.send((json.dumps({"result": "ko", "message": "Malformed command"}) + "\n").encode("utf-8"))
        return True

    result = True
    try:
        if cmd["context"] == "file":
            if cmd["command"]["name"] == "list":
                try:
                    res = files.List()
                    res.directory = cmd["command"]["directory"]
                    res.acl = cmd["command"]["acl"]

                    for item in res.get():
                        conn.send((item + "\n").encode("utf-8"))
                except ValueError as ex:
                    conn.send((json.dumps({"result": "ko", "message": str(ex)}) + "\n").encode("utf-8"))
            elif cmd["command"]["name"] == "get":
                res = files.Send()
                res.filename = cmd["command"]["filename"]

                for data in res.data():
                    conn.send(data)
            else:
                conn.send((json.dumps({"result": "ko", "message": "Command not found"}) + "\n").encode("utf-8"))
        elif cmd["context"] == "system":
            if cmd["command"]["name"] == "exec":
                conn.send(exec_command(cmd["command"]["value"]))
            elif cmd["command"]["name"] == "exit":
                result = False
        else:
            conn.send((json.dumps({"result": "ko", "message": "Context not found"}) + "\n").encode("utf-8"))
    except KeyError:
        logging.exception("KeyError Traceback and data: " + command.decode('utf-8'))
        conn.send((json.dumps({"result": "ko", "message": "Malformed command"}) + "\n").encode("utf-8"))

    return result

def serve(sock):
    sock.listen(1)

    execute = True
    while execute:
        conn, addr = sock.accept()

        try:
            data = conn.recv(4096)
            execute = parse(data, conn)
        except UnicodeDecodeError:
            pass
        except ssl.SSLError as err:
            print("SSL error: {0}".format(err))
        except OSError as err:
            print("Operating system error({0})".format(err))
        finally:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except:
                pass
            conn.close()

def go(sysargs):
    args = init_args().parse_args(sysargs)

    if args.ssl:
        cfg = configparser.ConfigParser()
        cfg.read(args.ssl)

        sslparams = {
            "enabled": True,
            "pem": cfg.get("ssl", "key"),
            "password": cfg.get("ssl", "password")
        }

        sock = get_socket(args.port, args.listen, sslparams)
        serve(sock)
    else:
        sslparams = {"enabled": False}
        sock = get_socket(args.port, args.listen, sslparams)
        serve(sock)

        sock.close()

if __name__ == "__main__":
    #import pycallgraph

    #pycallgraph.start_trace()

    go(sys.argv[1:])

    #pycallgraph.make_dot_graph('graph.png')

