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
import ptime as time
import os
import cPickle

import logging, logging_conf

import state
import identifier
from identifier import Id
import message
import token_manager
import tracker
from querier import Querier
from message import QUERY, RESPONSE, ERROR, OutgoingGetPeersQuery
from node import Node

#from profilestats import profile

logger = logging.getLogger('dht')

SAVE_STATE_DELAY = 1 * 60
STATE_FILENAME = 'state.dat'


#TIMEOUT_DELAY = 2

NUM_NODES = 8

class Controller:

    def __init__(self, dht_addr, state_filename,
                 routing_m_mod, lookup_m_mod,
                 private_dht_name):
        #TODO: don't do this evil stuff!!!
        message.private_dht_name = private_dht_name
        
        self.state_filename = state_filename
        saved_id, saved_nodes = state.load(self.state_filename)
        if saved_id:
            self._my_id = saved_id
            bootstrap_nodes = saved_nodes
            #TODO: include bootstrap nodes also because all saved nodes might
            #be down
        else:
            self._my_id = identifier.RandomId()
            bootstrap_nodes = BOOTSTRAP_NODES
        self._my_node = Node(dht_addr, self._my_id)
        self._tracker = tracker.Tracker()
        self._token_m = token_manager.TokenManager()

        self._querier = Querier()
        self._routing_m = routing_m_mod.RoutingManager(self._my_node, 
                                                       bootstrap_nodes)
        self._lookup_m = lookup_m_mod.LookupManager(self._my_id)
        current_ts = time.time()
        self._next_save_state_ts = current_ts + SAVE_STATE_DELAY
        self._next_main_loop_call_ts = 0
        self._pending_lookups = []
        '''        
    def finalize(self):
        #TODO2: stop each manager, save routing table
        return
        '''

    def get_peers(self, lookup_id, info_hash, callback_f, bt_port=0):
        """
        Start a get\_peers lookup whose target is 'info\_hash'. The handler
        'callback\_f' will be called with two arguments ('lookup\_id' and a
        'peer list') whenever peers are discovered. Once the lookup is
        completed, the handler will be called with 'lookup\_id' and None as
        arguments.

        This method is designed to be used as minitwisted's external handler.

        """
        logger.critical('get_peers %d %r' % (bt_port, info_hash))
        self._pending_lookups.append(self._lookup_m.get_peers(lookup_id,
                                                              info_hash,
                                                              callback_f,
                                                              bt_port))
        queries_to_send =  self._try_do_lookup()
        datagrams_to_send = self._register_queries(queries_to_send)
        return self._next_main_loop_call_ts, datagrams_to_send
        
    def _try_do_lookup(self):
        queries_to_send = []
        if self._pending_lookups:
            lookup_obj = self._pending_lookups[0]
        else:
            return queries_to_send
        log_distance = lookup_obj.info_hash.log_distance(self._my_id)
        bootstrap_rnodes = self._routing_m.get_closest_rnodes(log_distance,
                                                              8,
                                                              True)
        #TODO: remove magic number
        if bootstrap_rnodes:
            del self._pending_lookups[0]
            # look if I'm tracking this info_hash
            peers = self._tracker.get(lookup_obj.info_hash)
            callback_f = lookup_obj.callback_f
            if peers and callback_f and callable(callback_f):
                callback_f(lookup_obj.lookup_id, peers)
            # do the lookup
            queries_to_send = lookup_obj.start(bootstrap_rnodes)
        else:
            next_lookup_attempt_ts = time.time() + .2
            self._next_main_loop_call_ts = min(self._next_main_loop_call_ts,
                                               next_lookup_attempt_ts)
        return queries_to_send
        
    def print_routing_table_stats(self):
        self._routing_m.print_stats()

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

        logger.debug('main_loop BEGIN')
        queries_to_send = []
        current_ts = time.time()
        # At most, 10 seconds between calls to main_loop after the first call
        if current_ts > self._next_main_loop_call_ts:
            self._next_main_loop_call_ts = current_ts + 10
        else:
            # It's too early
            return self._next_main_loop_call_ts, []
        # Retry failed lookup (if any)
        queries_to_send.extend(self._try_do_lookup())
        # Take care of timeouts
        timeout_queries = self._querier.get_timeout_queries()
        for query in timeout_queries:
            queries_to_send.extend(self._on_timeout(query))

        # Routing table maintenance
        (maintenance_delay,
         queries,
         maintenance_lookup_target) = self._routing_m.do_maintenance()
        self._next_main_loop_call_ts = min(self._next_main_loop_call_ts,
                                           current_ts + maintenance_delay)
        queries_to_send.extend(queries)

        if maintenance_lookup_target:
            log_distance = maintenance_lookup_target.log_distance(
                self._my_id)
            bootstrap_rnodes = self._routing_m.get_closest_rnodes(
                log_distance, 8, True) #TODO: remove magic number
            lookup_obj = self._lookup_m.maintenance_lookup(
                maintenance_lookup_target)
            queries_to_send.extend(lookup_obj.start(bootstrap_rnodes))
            
        # Auto-save routing table
        if current_ts > self._next_save_state_ts:
            state.save(self._my_id,
                       self._routing_m.get_main_rnodes(),
                       self.state_filename)
            self._next_save_state_ts = current_ts + SAVE_STATE_DELAY
            self._next_main_loop_call_ts = min(self._next_main_loop_call_ts,
                                               self._next_save_state_ts)
        # Return control to reactor
        datagrams_to_send = self._register_queries(queries_to_send)
        return self._next_main_loop_call_ts, datagrams_to_send

    def _maintenance_lookup(self, target):
        self._lookup_m.maintenance_lookup(target)

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
            msg = message.IncomingMsg(datagram)
        except(message.MsgError):
            # ignore message
            return self._next_main_loop_call_ts, datagrams_to_send

        if msg.type == message.QUERY:
            if msg.src_id == self._my_id:
                logger.debug('Got a msg from myself:\n%r', msg)
                return self._next_main_loop_call_ts, datagrams_to_send
            response_msg = self._get_response(msg)
            if response_msg:
                bencoded_response = response_msg.stamp(msg.tid)
                datagrams_to_send.append(
                    message.Datagram(bencoded_response, addr))
            maintenance_queries_to_send = self._routing_m.on_query_received(
                msg.src_node)
            
        elif msg.type == message.RESPONSE:
            related_query = self._querier.get_related_query(msg)
            if not related_query:
                # Query timed out or unrequested response
                return self._next_main_loop_call_ts, datagrams_to_send
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

                if lookup_done:
                        queries_to_send = self._announce(
                            related_query.lookup_obj)
                        datagrams = self._register_queries(
                            queries_to_send)
                        datagrams_to_send.extend(datagrams)
                callback_f = related_query.lookup_obj.callback_f
                if callback_f and callable(callback_f):
                    lookup_id = related_query.lookup_obj.lookup_id
                    if peers:
                        callback_f(lookup_id, peers)
                    if lookup_done:
                        callback_f(lookup_id, None)
            # maintenance related tasks
            maintenance_queries_to_send = \
                self._routing_m.on_response_received(
                msg.src_node, related_query.rtt, msg.all_nodes)

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
                 ) = related_query.lookup_obj.on_error_received(msg)
                datagrams = self._register_queries(lookup_queries_to_send)
                datagrams_to_send.extend(datagrams)

                if lookup_done:
                    datagrams = self._announce(related_query.lookup_obj)
                    datagrams_to_send.extend(datagrams)
                callback_f = related_query.lookup_obj.callback_f
                if callback_f and callable(callback_f):
                    lookup_id = related_query.lookup_obj.lookup_id
                    if lookup_done:
                        callback_f(lookup_id, None)
            # maintenance related tasks
            maintenance_queries_to_send = \
                self._routing_m.on_error_received(addr)

        else: # unknown type
            return self._next_main_loop_call_ts, datagrams_to_send
        datagrams = self._register_queries(maintenance_queries_to_send)
        datagrams_to_send.extend(datagrams)
        return self._next_main_loop_call_ts, datagrams_to_send

    def _on_query_received(self):
        return
    def _on_response_received(self):
        return
    def _on_error_received(self):
        return
    
    
    def _get_response(self, msg):
        if msg.query == message.PING:
            return message.OutgoingPingResponse(msg.src_node, self._my_id)
        elif msg.query == message.FIND_NODE:
            log_distance = msg.target.log_distance(self._my_id)
            rnodes = self._routing_m.get_closest_rnodes(log_distance,
                                                       NUM_NODES, False)
            return message.OutgoingFindNodeResponse(msg.src_node,
                                                    self._my_id,
                                                    rnodes)
        elif msg.query == message.GET_PEERS:
            token = self._token_m.get()
            log_distance = msg.info_hash.log_distance(self._my_id)
            rnodes = self._routing_m.get_closest_rnodes(log_distance,
                                                       NUM_NODES, False)
            peers = self._tracker.get(msg.info_hash)
            if peers:
                logger.debug('RESPONDING with PEERS:\n%r' % peers)
            return message.OutgoingGetPeersResponse(msg.src_node,
                                                    self._my_id,
                                                    token,
                                                    nodes=rnodes,
                                                    peers=peers)
        elif msg.query == message.ANNOUNCE_PEER:
            peer_addr = (msg.src_addr[0], msg.bt_port)
            self._tracker.put(msg.info_hash, peer_addr)
            return message.OutgoingAnnouncePeerResponse(msg.src_node,
                                                        self._my_id)
        else:
            logger.debug('Invalid QUERY: %r' % (msg.query))
            #TODO: maybe send an error back?
        
    def _on_response_received(self, msg):
        pass

    def _on_timeout(self, related_query):
        queries_to_send = []
        if related_query.lookup_obj:
            (lookup_queries_to_send,
             num_parallel_queries,
             lookup_done
             ) = related_query.lookup_obj.on_timeout(related_query.dst_node)
            queries_to_send.extend(lookup_queries_to_send)
            callback_f = related_query.lookup_obj.callback_f
            if lookup_done and callback_f and callable(callback_f):
                queries_to_send.extend(self._announce(
                        related_query.lookup_obj))
                lookup_id = related_query.lookup_obj.lookup_id
                related_query.lookup_obj.callback_f(lookup_id, None)
        queries_to_send.extend(
            self._routing_m.on_timeout(related_query.dst_node))
        return queries_to_send

    def _announce(self, lookup_obj):
        queries_to_send, announce_to_myself = lookup_obj.announce()
        return queries_to_send
        '''
        if announce_to_myself:
            self._tracker.put(lookup_obj._info_hash,
                              (self._my_node.addr[0], lookup_obj._bt_port))
        '''
        
    def _register_queries(self, queries_to_send, lookup_obj=None):
        if not queries_to_send:
            return []
        timeout_call_ts, datagrams_to_send = self._querier.register_queries(
            queries_to_send)
        self._next_main_loop_call_ts = min(self._next_main_loop_call_ts,
                                           timeout_call_ts)
        return datagrams_to_send
                    
        
BOOTSTRAP_NODES = (
    Node(('67.215.242.138', 6881)), #router.bittorrent.com
    Node(('192.16.127.98', 7000)), #KTH node
    )
