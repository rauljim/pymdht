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
from core.message import MsgFactory, Datagram, IncomingMsg
from core.identifier import RandomId
from core.minitwisted import ThreadedReactor
import core.ptime as time
from core.pymdht import PYMDHT_VERSION

MY_ID = RandomId()
TID = '11'

INPUT_FILE = '../core/bootstrap.backup'
PORT = 7667

TIMEOUT = .25 # seconds

MAX_NODES = 2000

class NodeCrawler(object):

    def __init__(self, filename):
        self.msg_f = MsgFactory(PYMDHT_VERSION, MY_ID)
        self._lock = threading.Lock()
        self._is_done = False
        self._pinged_ips = set()
        self._pinged_addrs = set()
        self._ok_addrs = set()
        self._found_nodes = []
        self._file = open(filename)
        self.reactor = ThreadedReactor(
            self._main_loop,
            PORT, self._on_datagram_received)
        self.reactor.start()

    def _get_node_from_file(self):
        try:
            line = self._file.next()
        except (StopIteration):
            return
        ip, str_port = line.split()
        return Node((ip, int(str_port)))

    def _get_found_node(self):
        if len(self._ok_addrs) < MAX_NODES and self._found_nodes:
            return self._found_nodes.pop(0)
                        
    def _get_ping_datagram(self):
        datagram = None
        node_ = self._get_node_from_file()
        if not node_:
            node_ = self._get_found_node()
        if node_:
            if node_.ip in self._pinged_ips:
                #duplicated IP, ignore
                return
            print '>>>>', node_, len(self._ok_addrs), len(self._found_nodes)
            msg = self.msg_f.outgoing_find_node_query(node_,
                                                      RandomId())
            datagram = Datagram(msg.stamp(TID), node_.addr)
        else:
            with self._lock:                                                                        
                self._is_done = True  
        return datagram
        
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
        if len(self._found_nodes) < MAX_NODES:
            msg = IncomingMsg(None, datagram)
            if msg.all_nodes:
                self._found_nodes.extend(msg.all_nodes)
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
    if len(sys.argv) > 1:
        input_filename = sys.argv[1]
    else:
        input_filename = INPUT_FILE
    output_filename = 'crawled.nodes.release-%d.%d.%d' % (
        PYMDHT_VERSION)
    nc = NodeCrawler(input_filename)
    while not nc.is_done():
        time.sleep(1)
    time.sleep(3)
    result = nc.stop_and_get_result()
    output_file = open(output_filename, 'w')
    for addr in result:
        print >>output_file, addr[0], addr[1]
