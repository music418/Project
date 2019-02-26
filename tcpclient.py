#!/usr/bin/env python

import threading
import socket
import select
import sys
import time
import binascii
import traceback
import struct
import re

class R():
    logFile = None
    @staticmethod
    def log(*msg):
        a0 = (time.ctime(),) + msg
        print a0
        if R.logFile:
            R.logFile.write(str(a0) + "\r\n")
            R.logFile.flush()
    @staticmethod        
    def debug(*msg):
        R.log(*msg)

class Camera():
    def __init__(self, **kwargs):
        self.cmds = []
        self.index = 0
        path = kwargs.get('path', "camera.txt")
        file = open(path)
        while True:
            line = file.readline()
            if not line:
                break
            line = line.strip("\n")
            self.cmds.append({"cmd": line})
            # R.log(line)
        file.close()
        # R.log(self.cmds)

    def cmd(self):
        self.index = 0
        if self.index >= len(self.cmds):
            self.index = 0
        data = binascii.unhexlify(self.cmds[self.index]["cmd"])
        return data
        
class TcpClient(threading.Thread):
    def __init__(self, **kwargs):
        self.addr = kwargs.get('addr', ("127.0.0.1", 10086))
        self.timeout = kwargs.get('timeout', 2)
        self.socket = None
        self.cmds = []
        self.camera = Camera()
        
    def handler(self):
        inputs = [self.socket]
        readable, writable, exceptional = select.select(inputs, [], [], self.timeout)
        if not readable:
            # R.debug("time out ", self.addr)
            data = self.camera.cmd()
            self.socket.send(data)
            R.debug("snd", binascii.hexlify(data))
        for s in readable:
            data = ""
            try:
                data = s.recv(1024)
            except Exception, e:
                R.debug(e)
                s.close()
                self.socket = None
                return
            if len(data) <= 0:
                s.close()
                self.socket = None
                return
            R.debug("rcv", binascii.hexlify(data))

    def run(self):
        while True:
            if self.connect():
                self.handler()
        
    def connect(self):
        if self.socket:
            return self.socket
        time.sleep(1)
        for res in socket.getaddrinfo(self.addr[0], self.addr[1], socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                sock = socket.socket(af, socktype, proto)
                sock.settimeout(self.timeout)
            except socket.error, msg:
                continue
            try:
                sock.connect(sa)
            except socket.error, msg:
                sock.close()
                sock = None
                # R.log("connect error", self.addr)
                continue
            break
        if sock:
            self.socket = sock
            R.log("client create ok", self.addr)
        else:
            R.log("client create error", self.addr)
        return self.socket
        
    def send(self, data):
        self.socket.send(data)
        
    def recv(self, count=1):
        return self.socket.recv(count)
      
    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None

if __name__ == "__main__":
    client = TcpClient(addr=("192.168.1.109", 30001))
    # client = TcpClient(addr=("192.168.0.110", 10086))
    client.run()

