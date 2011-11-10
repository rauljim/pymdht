#! /usr/bin/env python

# Copyright (C) 2011 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import threading
import sys
sys.path.append('..')
import logging

from core.pymdht import PYMDHT_VERSION
import core.logging_conf as logging_conf
from core.node import Node
from core.message import MsgFactory, Datagram
from core.identifier import RandomId
from core.minitwisted import ThreadedReactor
import core.ptime as time

MY_ID = RandomId()
TID = '11'

INPUT_FILE = '../core/bootstrap.backup'
PORT = 7667

TIMEOUT = .25 # seconds

class BootstrapChecker(object):

    def __init__(self, filename):
        self.msg_f = MsgFactory(PYMDHT_VERSION, MY_ID)
        self._lock = threading.Lock()
        self._is_done = False
        self._pinged_ips = set()
        self._pinged_addrs = set()
        self._ok_addrs = set()
        self._file = open(filename)
        self.reactor = ThreadedReactor(
            self._main_loop,
            PORT, self._on_datagram_received)
        self.reactor.start()


    def _get_ping_datagram(self):
        try:
            line = self._file.next()
        except (StopIteration):
            with self._lock:
                self._is_done = True
                return
        print '>>>>', line
        ip, str_port = line.split()
        if ip in self._pinged_ips:
            #duplicated IP, ignore
            return
        addr = (ip, int(str_port))
        msg = self.msg_f.outgoing_ping_query(Node(addr))
        return Datagram(msg.stamp(TID), addr)
        
    def _main_loop(self):
        datagrams_to_send = []
        datagram = self._get_ping_datagram()
        if datagram:
            self._pinged_ips.add(datagram.addr[0])
            self._pinged_addrs.add(datagram.addr)
            datagrams_to_send.append(datagram)
        return TIMEOUT, datagrams_to_send

    def _on_datagram_received(self, datagram):
        addr = datagram.addr
        if addr in self._pinged_addrs:
            self._pinged_addrs.remove(addr)
            self._ok_addrs.add(addr)
        return TIMEOUT, []
        
            
    def is_done(self):
        with self._lock:
            done = self._is_done
        return done

    def stop_and_get_result(self):
        self.reactor.stop()
        return sorted(list(self._ok_addrs))

if __name__ == '__main__':
    logging_conf.setup('.', logging.DEBUG)
    bc = BootstrapChecker(sys.argv[1])
    while not bc.is_done():
        time.sleep(1)
    time.sleep(3)
    result = bc.stop_and_get_result()
    for addr in result:
        print addr[0], addr[1]
