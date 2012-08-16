#! /usr/bin/env python

# Copyright (C) 2011 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import threading
import sys
sys.path.append('..')
import logging
import socket

from core.pymdht import PYMDHT_VERSION, VERSION_LABEL
import core.logging_conf as logging_conf
from core.node import Node
from core.message import MsgFactory, Datagram, IncomingMsg, MsgError
from core.identifier import RandomId
from core.minitwisted import ThreadedReactor
import core.ptime as time
from core.pymdht import PYMDHT_VERSION
import core.utils as utils

MY_ID = RandomId()
TID = '11'

INPUT_FILE = '../core/bootstrap_unstable'
output_filename = 'crawled24.nodes.release-%d.%d.%d' % (
        PYMDHT_VERSION)
PORT = 7667

TIMEOUT = .5 # seconds

MAX_NODES = 5000

MIN_CHECKING_INTERVAL = 60 * 60
OK_CHECKING_PERIOD = 50 * 3600

class NodeCrawler(object):

    def __init__(self, filename):
        self.msg_f = MsgFactory(VERSION_LABEL, MY_ID)
        self._lock = threading.Lock()
        self._is_done = False
        self._queued_addrs = []
        self._checking_rnodes = []
        self._pinging_rnode = None
        self._pinged_ips = set()
        self._checking_and_ok_subnets = set()
        self._num_ok_addrs = 0
        self._next_main_loop_ts = time.time()
        self._output_file = open(output_filename, 'w')
        input_file = open(filename)
        for line in input_file:
            ip, str_port = line.split()
            self._queued_addrs.append((ip, int(str_port)))
        self.reactor = ThreadedReactor(
            self._main_loop,
            PORT, self._on_datagram_received)
        
    def start(self):
        while self._num_ok_addrs < MAX_NODES:
            self.reactor.run_one_step()

    def _get_found_node(self):
        if len(self._ok_subnet_addrs) < MAX_NODES and self._found_nodes:
            return self._found_nodes.pop(0)
                        
    def _get_ping_datagram(self):
        datagram = None
        rnode = None
        if self._checking_rnodes:
            checking_rnode = self._checking_rnodes[0]
            if time.time() > checking_rnode.last_seen + MIN_CHECKING_INTERVAL:
                # ping this node again
                del self._checking_rnodes[0]
                rnode = checking_rnode
        while not rnode and self._queued_addrs:
            addr = self._queued_addrs.pop(0)
            subnet = utils.get_subnet(addr)
            if addr[0] not in self._pinged_ips and subnet not in self._checking_and_ok_subnets:
                self._pinged_ips.add(addr[0])
                self._checking_and_ok_subnets.add(subnet)
                rnode = Node(addr).get_rnode(0)
        if rnode:
            self._pinging_rnode = rnode
            print '%28r %2.2f hours|| queue: %d, pinged: %d, checking: %d, ok: %d' % (
                rnode.addr,
                (time.time() - rnode.creation_ts) / 3600,
                len(self._queued_addrs),
                len(self._pinged_ips),
                len(self._checking_rnodes),
                self._num_ok_addrs),
            msg = self.msg_f.outgoing_find_node_query(rnode,
                                                      RandomId())
            datagram = Datagram(msg.stamp(TID), rnode.addr)
        return datagram

    def _main_loop(self):
        if self._pinging_rnode:
            #no response received: consider it dead
            print 'DEAD'
            subnet = utils.get_subnet(self._pinging_rnode.addr)
            self._checking_and_ok_subnets.remove(subnet)
            self._pinging_rnode = None
            
        datagrams_to_send = []
        datagram = self._get_ping_datagram()
        if datagram:
            self._pinged_ips.add(datagram.addr[0])
            datagrams_to_send.append(datagram)
        self._next_main_loop_ts = time.time() + TIMEOUT
        return  self._next_main_loop_ts, datagrams_to_send

    def _on_datagram_received(self, datagram):
        #TODO: do not add to UNSTABLE if node is alredy in STABLE
        addr = datagram.addr
        subnet = utils.get_subnet(addr)
        if self._pinging_rnode and addr == self._pinging_rnode.addr:
            print 'ALIVE'
            # node is alive
            self.last_seen = time.time()
            if time.time() > self._pinging_rnode.creation_ts + OK_CHECKING_PERIOD:
                self._num_ok_addrs += 1
                print >>self._output_file, addr[0], addr[1]
            else:
                self._checking_rnodes.append(self._pinging_rnode)
            self._pinging_rnode = None
            self._checking_and_ok_subnets.add(subnet)
        if len(self._queued_addrs) < MAX_NODES:
            try:
                msg = IncomingMsg(None, datagram)
                for node_ in msg.all_nodes or []:
                    if node_.addr[0] not in self._pinged_ips and utils.get_subnet(
                        node_.addr) not in self._checking_and_ok_subnets:
                        self._queued_addrs.append(node_.addr)
            except (MsgError):
                print 'MsgError'
        return self._next_main_loop_ts, []
        
            
    def is_done(self):
        with self._lock:
            done = self._is_done
        return done

    def stop_and_get_result(self):
        self.reactor.stop()
        return sorted(self._ok_subnet_addrs.values())

if __name__ == '__main__':
    logging_conf.setup('.', logging.DEBUG)
    if len(sys.argv) > 1:
        input_filename = sys.argv[1]
    else:
        input_filename = INPUT_FILE
    nc = NodeCrawler(input_filename)
    nc.start()
