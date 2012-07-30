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

import sys
import ptime as time
import datetime
import os
import cPickle

import logging, logging_conf

import identifier
from identifier import Id
import message
from querier import Querier
from message import QUERY, RESPONSE, ERROR
from node import Node
import bootstrap
#import pkgutil

#from profilestats import profile

logger = logging.getLogger('dht')


class Controller:

    def __init__(self, version_label,
                 my_node, conf_path,
                 routing_m_mod, lookup_m_mod,
                 experimental_m_mod,
                 private_dht_name,
                 bootstrap_mode):
        self.bootstrapper = bootstrap.OverlayBootstrapper(conf_path)
        my_addr = my_node.addr
        self._my_id = my_node.id # id indicated by user 
        if not self._my_id:
            self._my_id = self._my_id = identifier.RandomId() # random id
        self._my_node = Node(my_addr, self._my_id, version=version_label)
        self.msg_f = message.MsgFactory(version_label, self._my_id,
                                        private_dht_name)
        self._querier = Querier()
        self._routing_m = None
        self._lookup_m = lookup_m_mod.LookupManager(self._my_id, self.msg_f,
                                                    self.bootstrapper)
        self._experimental_m = None
                  
        current_ts = time.time()
        self._next_maintenance_ts = current_ts
        self._next_timeout_ts = current_ts
        self._next_main_loop_call_ts = current_ts
           
    def on_stop(self):
        self.bootstrapper.save_to_file()

    def get_peers(self, lookup_id, info_hash, callback_f, bt_port, use_cache):
        """
        Start a get\_peers lookup whose target is 'info\_hash'. The handler
        'callback\_f' will be called with three arguments ('lookup\_id',
        'peers', 'node') whenever peers are discovered. Once the lookup is
        completed, the handler will be called with arguments:
        ('lookup\_id', None, None).

        This method is called by minitwisted, using the minitwisted thread.

        """
        datagrams_to_send = []
        logger.debug('get_peers %d %r' % (bt_port, info_hash))
        lookup_obj = self._lookup_m.get_peers(lookup_id,
                                              info_hash,
                                              callback_f,
                                              bt_port)
        queries_to_send = []
        distance = lookup_obj.info_hash.distance(self._my_id)
        bootstrap_rnodes = []
        # do the lookup
        # NOTE: if bootstrap_rnodes is empty, a OVERLAY BOOTSTRAP will be
        # done.
        queries_to_send = lookup_obj.start(bootstrap_rnodes, self.bootstrapper)

        datagrams_to_send = self._register_queries(queries_to_send)
        return datagrams_to_send
    
    def main_loop(self):
        """
        Perform maintenance operations. The main operation is routing table
        maintenance where staled nodes are added/probed/replaced/removed as
        needed. The routing management module specifies the implementation
        details.  This includes keeping track of queries that have not been
        responded for a long time (timeout) with the help of
        querier.Querier. The routing manager and the lookup manager will be
        informed of those timeouts.

        This method is designed to be used as minitwisted's heartbeat handler.

        """

        queries_to_send = []
        current_ts = time.time()
        #TODO: I think this if should be removed
        # At most, 1 second between calls to main_loop after the first call
        if current_ts >= self._next_main_loop_call_ts:
            self._next_main_loop_call_ts = current_ts + 1
        else:
            # It's too early
            return self._next_main_loop_call_ts, []
        
        # Take care of timeouts
        if current_ts >= self._next_timeout_ts:
            (self._next_timeout_ts,
             timeout_queries) = self._querier.get_timeout_queries()
            for query in timeout_queries:
                queries_to_send.extend(self._on_timeout(query))

        # Return control to reactor
        datagrams_to_send = self._register_queries(queries_to_send)
        return self._next_main_loop_call_ts, datagrams_to_send

    def on_datagram_received(self, datagram):
        """
        Perform the actions associated to the arrival of the given
        datagram. The datagram will be ignored in cases such as invalid
        format. Otherwise, the datagram will be decoded and different modules
        will be informed to take action on it. For instance, if the datagram
        contains a response to a lookup query, both routing and lookup manager
        will be informed. Additionally, if that response contains peers, the
        lookup's handler will be called (see get\_peers above).
        This method is designed to be used as minitwisted's networking handler.

        """
        data = datagram.data
        addr = datagram.addr
        datagrams_to_send = []
        try:
            msg = self.msg_f.incoming_msg(datagram)
            
        except(message.MsgError):
            # ignore message
            return self._next_main_loop_call_ts, datagrams_to_send

        if msg.type == message.QUERY:
            # Ignore
            return self._next_main_loop_call_ts, datagrams_to_send

        elif msg.type == message.RESPONSE:
            related_query = self._querier.get_related_query(msg)
            if not related_query:
                # Query timed out or unrequested response
                return self._next_main_loop_call_ts, datagrams_to_send
            #TODO: you need to get datagrams to be able to send messages (raul)
            # lookup related tasks
            if related_query.lookup_obj:
                (lookup_queries_to_send,
                 peers,
                 num_parallel_queries,
                 lookup_done
                 ) = related_query.lookup_obj.on_response_received(
                    msg, msg.src_node)
                datagrams = self._register_queries(lookup_queries_to_send)
                datagrams_to_send.extend(datagrams)

                lookup_obj = related_query.lookup_obj
                lookup_id = lookup_obj.lookup_id
                callback_f = lookup_obj.callback_f
                if peers:
                    if callback_f and callable(callback_f):
                        callback_f(lookup_id, peers, msg.src_node)
                if lookup_done:
                    if callback_f and callable(callback_f):
                        callback_f(lookup_id, None, msg.src_node)
                    queries_to_send = self._announce(
                        related_query.lookup_obj)
                    datagrams = self._register_queries(
                        queries_to_send)
                    datagrams_to_send.extend(datagrams)
                    
        elif msg.type == message.ERROR:
            related_query = self._querier.get_related_query(msg)
            if not related_query:
                # Query timed out or unrequested response
                return self._next_main_loop_call_ts, datagrams_to_send
            # lookup related tasks
            if related_query.lookup_obj:
                peers = None # an error msg doesn't have peers
                (lookup_queries_to_send,
                 num_parallel_queries,
                 lookup_done
                 ) = related_query.lookup_obj.on_error_received(msg, addr)
                datagrams = self._register_queries(lookup_queries_to_send)
                datagrams_to_send.extend(datagrams)

                callback_f = related_query.lookup_obj.callback_f
                if callback_f and callable(callback_f):
                    lookup_id = related_query.lookup_obj.lookup_id
                    if lookup_done:
                        callback_f(lookup_id, None, msg.src_node)
                if lookup_done:
                    datagrams = self._announce(related_query.lookup_obj)
                    datagrams_to_send.extend(datagrams)

        else: # unknown type
            return self._next_main_loop_call_ts, datagrams_to_send
        return self._next_main_loop_call_ts, datagrams_to_send

    def _on_query_received(self):
        return
    def _on_response_received(self):
        return
    def _on_error_received(self):
        return

    def _on_timeout(self, related_query):
        queries_to_send = []
        #TODO: on_timeout should return queries (raul)
        if related_query.lookup_obj:
            (lookup_queries_to_send,
             num_parallel_queries,
             lookup_done
             ) = related_query.lookup_obj.on_timeout(related_query.dst_node)
            queries_to_send.extend(lookup_queries_to_send)
            callback_f = related_query.lookup_obj.callback_f
            if lookup_done:
                lookup_id = related_query.lookup_obj.lookup_id
                if callback_f and callable(callback_f):
                    related_query.lookup_obj.callback_f(lookup_id, None, None)
                queries_to_send.extend(self._announce(
                        related_query.lookup_obj))
        return queries_to_send

    def _announce(self, lookup_obj):
        queries_to_send, announce_to_myself = lookup_obj.announce()
        return queries_to_send
    
    def _register_queries(self, queries_to_send, lookup_obj=None):
        if not queries_to_send:
            return []
        timeout_call_ts, datagrams_to_send = self._querier.register_queries(
            queries_to_send)
        self._next_main_loop_call_ts = min(self._next_main_loop_call_ts,
                                           timeout_call_ts)
        return datagrams_to_send
    
