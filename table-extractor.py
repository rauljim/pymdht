#! /usr/bin/env python

# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
The controller module is designed to be the central point where most modules
are connected. This module delegates most of the implementation details to
other modules. This delegation model creates separated responsibility areas
where implementation can be changed in isolation.

The extreme cases are the plug-ins which allow us to develop/run different
implementations of routing and lookup managers in parallel.

"""

size_estimation = False

import sys
import core.ptime as time
import datetime
import os
import cPickle
import core.ptime as time
import sys, os
from optparse import OptionParser
import logging

import core.logging_conf as logging_conf
from core.identifier import Id, RandomId
import core.message as message
from core.querier import Querier
from core.message import QUERY, RESPONSE, ERROR
from core.node import Node
import core.minitwisted as minitwisted

logger = logging.getLogger('dht')

PYMDHT_VERSION = (11, 12, 1)

PING = False

class TableExtractor:

    def __init__(self, node_to_extract):
        self.node_to_extract = node_to_extract
        self.my_id = self._my_id = RandomId()
        self.msg_f = message.MsgFactory(PYMDHT_VERSION, self.my_id,
                                        None)
        self.querier = Querier()
        self.next_level = 159
        self.last_extraction_ts = 0
                
    def on_stop(self):
        pass#self._experimental_m.on_stop()

    def main_loop(self):
        msgs_to_send = []
        current_time = time.time()
        if current_time > self.last_extraction_ts + 1:
            fn_msg = self.msg_f.outgoing_find_node_query(
                self.node_to_extract,
                self.node_to_extract.id.generate_close_id(self.next_level),
                None,
                None)
            if PING:
                fn_msg = self.msg_f.outgoing_ping_query(
                    self.node_to_extract,
                    None)
            msgs_to_send.append(fn_msg)
            self.last_extraction_ts = current_time
            self.next_level -= 1
        # Take care of timeouts
        (self._next_timeout_ts,
        timeout_queries) = self.querier.get_timeout_queries()
        for query in timeout_queries:
            print 'TIMEOUT'
        timeout_call_ts, datagrams_to_send = self.querier.register_queries(
            msgs_to_send)
        return self.last_extraction_ts + 1, datagrams_to_send

    def on_datagram_received(self, datagram):
        data = datagram.data
        addr = datagram.addr
        datagrams_to_send = []
        try:
            msg = self.msg_f.incoming_msg(datagram)
        except(message.MsgError):
            # ignore message
            return self._next_main_loop_call_ts, datagrams_to_send

        if msg.type == message.RESPONSE:
            related_query = self.querier.get_related_query(msg)
            if related_query and related_query.query == message.FIND_NODE:
                print 'level', msg.version
                for node_ in msg.nodes:
                    print node_
            else:
                print 'not related'
        return self.last_extraction_ts + 1, datagrams_to_send

    
def main(options, args):
    id_str, ip, port_str = args
    port = int(port_str)
    node_to_extract = Node((ip, port), Id(id_str))
    table_extractor = TableExtractor(node_to_extract)

    logs_path = os.path.join(os.path.expanduser('~'), '.pymdht')
    logging_conf.setup(logs_path, logging.DEBUG)
    reactor = minitwisted.ThreadedReactor(
    table_extractor.main_loop, 7000, 
    table_extractor.on_datagram_received)
    reactor.start()
    time.sleep(30)
        
if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    main(options, args)


