# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
This module is the API for the whole package.

You can use the Pymdht class and its methods to interact with
the DHT.

Find usage examples in server_dht.py and interactive_dht.py.

"""

import sys
import os
import ptime as time

import minitwisted
import controller
import logging, logging_conf
import swift_tracker

logger = logging.getLogger('dht')

PYMDHT_VERSION = (12, 11, 1)
VERSION_LABEL = ''.join(
    ['NS',
     chr((PYMDHT_VERSION[0] - 11) * 24 + PYMDHT_VERSION[1]),
     chr(PYMDHT_VERSION[2])
     ])


class Pymdht:
    """Pymdht is the interface for the whole package.

    Setting up the DHT node is as simple as creating this object.
    The parameters are:
    - my_node: a Node object containing IP address and port number (id is optional).
    - conf_path: the complete path to local files (logs, bootstrap.local, etc.)
    - routing_m_mod: the module implementing routing management.
    - lookup_m_mod: the module implementing lookup management.
    - experimental_m_mod: the module implementing experimental management.
    - private_dht_name: name of the private DHT (use global DHT when None)
    - debug_level: level of logs saved into pymdht.log (standard logging module).
    - auto_bootstrap: perform a lookup on node's id to bootstrap into the overlay
    - bootstrap_mode: (only if YOU want to run a stablebootstrap node)
    - swift_port: UDP port for Swift interface (used in Android app)
    """
    def __init__(self, my_node, conf_path,
                 routing_m_mod, lookup_m_mod,
                 experimental_m_mod,
                 private_dht_name,
                 debug_level,
                 auto_bootstrap=True,
                 bootstrap_mode=False,
                 swift_port=0):
        logging_conf.setup(conf_path, debug_level)
        self.controller = controller.Controller(VERSION_LABEL,
                                                my_node, conf_path,
                                                routing_m_mod,
                                                lookup_m_mod,
                                                experimental_m_mod,
                                                private_dht_name,
                                                bootstrap_mode)
        self.reactor = minitwisted.ThreadedReactor(
            self.controller.main_loop,
            my_node.addr[1], self.controller.on_datagram_received)

        self.swift_tracker_thread = None
        if swift_port:
            print 'Creating SwiftTracker'
            self.swift_tracker_thread = swift_tracker.SwiftTracker(self, swift_port)
            self.swift_tracker_thread.start()
        self.timestamps = []
        self.max_num_sec = 0
        self.max_num_min = 0
        self.max_num_10min = 0
        if auto_bootstrap:
            # Overlay bootstrap
            self.get_peers(None, self.controller._my_id, None, 0)
        self.reactor.start()

    def stop(self):
        """Stop the DHT node."""
        # TODO: notify controller so it can do cleanup?
        self.reactor.stop()
        # No need to call_asap because the minitwisted thread is dead by now
        self.controller.on_stop()
        if self.swift_tracker_thread:
            self.swift_tracker_thread.stop()

        logging_conf.close()

    def get_peers(self, lookup_id, info_hash, callback_f,
                  bt_port=0, use_cache=False):
        """ Start a get peers lookup. Return a Lookup object.
        
        The info_hash must be an identifier.Id object.
        
        The callback_f must expect two parameters (lookup_id and list of
        peeers). When peers are discovered, the callback is called with a list
        of peers as paramenter.  The list of peers is a list of addresses
        (<IPv4, port> pairs).

        The bt_port parameter is optional. When non-zero, ANNOUNCE messages
        will be send using the provided port number.

        Notice that the callback can be fired even before this call ends. Your
        callback needs to be ready to get peers BEFORE calling this fuction.
        
        """
        # logger.critical("pymdht.get_peers: callback: %r" % (callback_f))
        current_time = time.time()
        self.timestamps.append(current_time)
        num_sec = 0
        num_min = 0
        num_10min = 0
        for ts in self.timestamps:
            if current_time < ts + 10 * 60:
                num_10min += 1
                if current_time < ts + 60:
                    num_min += 1
                    if current_time < ts + 1:
                        num_sec += 1
        self.max_num_sec = max(self.max_num_sec, num_sec)
        self.max_num_min = max(self.max_num_min, num_min)
        self.max_num_10min = max(self.max_num_10min, num_10min)
        self.timestamps = self.timestamps[-num_10min:]
        logger.info("%d(%d) %d(%d) %d(%d) --- %r callback: %r" % (
                num_sec, self.max_num_sec,
                num_min, self.max_num_min,
                num_10min, self.max_num_10min,
                info_hash, callback_f))

        use_cache = True
        print 'pymdht: use_cache ON!!'
        self.reactor.call_asap(self.controller.get_peers,
                               lookup_id, info_hash,
                               callback_f, bt_port,
                               use_cache)

    def print_routing_table_stats(self):
        self.controller.print_routing_table_stats()

    def print_routing_table(self):
        self.controller.print_routing_table()

    def start_capture(self):
        self.reactor.start_capture()

    def stop_and_get_capture(self):
        return self.reactor.stop_and_get_capture()
