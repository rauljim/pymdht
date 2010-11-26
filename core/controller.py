# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import ptime as time
import os
import cPickle

import logging, logging_conf

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

    def __init__(self, dht_addr, state_path,
                 routing_m_mod, lookup_m_mod,
                 private_dht_name):
        #TODO: don't do this evil stuff!!!
        message.private_dht_name = private_dht_name
        
        self.state_filename = os.path.join(state_path, STATE_FILENAME)
        self.load_state()
        if not self._my_id:
            self._my_id = identifier.RandomId()
        self._my_node = Node(dht_addr, self._my_id)
        self._tracker = tracker.Tracker()
        self._token_m = token_manager.TokenManager()

        self._querier = Querier(self._my_id)
        bootstrap_nodes = self.loaded_nodes or BOOTSTRAP_NODES
        del self.loaded_nodes
        self._routing_m = routing_m_mod.RoutingManager(self._my_node, 
                                                       bootstrap_nodes)
        self._lookup_m = lookup_m_mod.LookupManager(self._my_id)
        current_ts = time.time()
        self._next_save_state_ts = current_ts + SAVE_STATE_DELAY
        self._next_main_loop_call_ts = 0
        self._next_lookup_attempt_ts = 0
        self._pending_lookups = []
        
    def finalize(self):
        #TODO2: stop each manager, save routing table
        return

    def save_state(self):
        rnodes = self._routing_m.get_main_rnodes()
        f = open(self.state_filename, 'w')
        f.write('%r\n' % self._my_id)
        for rnode in rnodes:
            f.write('%d\t%r\t%s\t%d\t%f\n' % (
                    self._my_id.log_distance(rnode.id),
                    rnode.id, rnode.addr[0], rnode.addr[1],
                    rnode.rtt * 1000))
        f.close()

    def load_state(self):
        self._my_id = None
        self.loaded_nodes = []
        try:
            f = open(self.state_filename)
        except(IOError):
            return
        # the first line contains this node's identifier
        hex_id = f.readline().strip()
        self._my_id = Id(hex_id)
        # the rest of the lines contain routing table nodes
        # FORMAT
        # log_distance hex_id ip port rtt
        for line in f:
            _, hex_id, ip, port, _ = line.split()
            addr = (ip, int(port))
            node_ = Node(addr, Id(hex_id))
            self.loaded_nodes.append(node_)
        f.close
        
    def get_peers(self, lookup_id, info_hash, callback_f, bt_port=0):
        logger.critical('get_peers %d %r' % (bt_port, info_hash))
        self._pending_lookups.append(self._lookup_m.get_peers(lookup_id,
                                                              info_hash,
                                                              callback_f,
                                                              bt_port))
        return self._next_main_loop_call_ts, self._try_do_lookup()
        
    def _try_do_lookup(self):
        msgs_to_send = []
        if (self._next_lookup_attempt_ts and
            time.time() < self._next_lookup_attempt_ts):
            # It's too early to retry this lookup
            return msgs_to_send
        if self._pending_lookups:
            lookup_obj = self._pending_lookups[0]
        else:
            return msgs_to_send
        log_distance = lookup_obj.info_hash.log_distance(self._my_id)
        bootstrap_rnodes = self._routing_m.get_closest_rnodes(log_distance,
                                                              None,
                                                              True)
        if bootstrap_rnodes:
            del self._pending_lookups[0]
            # look if I'm tracking this info_hash
            peers = self._tracker.get(info_hash)
            callback_f = lookup_obj.callback_f
            if peers and callback_f and callable(callback_f):
                callback_f(lookup_id, peers)
            # do the lookup
            queries_to_send = lookup_obj.start(bootstrap_rnodes)
            msgs_to_send = self._register_queries(queries_to_send)
            self._next_lookup_attempt_ts = None
        else:
            self._next_lookup_attempt_ts = time.time() + .2
            self._next_main_loop_call_ts = min(self._next_main_loop_call_ts,
                                               self._next_lookup_attempt_ts)
        return msgs_to_send
        
    def print_routing_table_stats(self):
        self._routing_m.print_stats()

    def main_loop(self):
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
        self._try_do_lookup()
        # Take care of timeouts
        timeout_queries = self._querier.get_timeout_queries()
        for query in timeout_queries:
            if query.lookup_obj:
                queries_to_send.extend(query.lookup_obj.on_timeout())
            queries_to_send.extend(self._routing_m.on_timeout(query.dstnode))
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
            raise Exception
            self.save_state()
            self._next_save_state_ts = current_ts + SAVE_STATE_DELAY
            self._next_main_loop_call_ts = min(self._next_main_loop_call_ts,
                                               self._next_save_state_ts)
        # Return control to reactor
        msgs_to_send = self._register_queries(queries_to_send)
        return self._next_main_loop_call_ts, msgs_to_send

    def _maintenance_lookup(self, target):
        self._lookup_m.maintenance_lookup(target)

    def on_datagram_received(self, data, addr):
        msgs_to_send = []
        try:
            msg = message.IncomingMsg(data, addr)
        except(message.MsgError):
            # ignore message
            return self._next_main_loop_call_ts, msgs_to_send

        if msg.type == message.QUERY:
            if msg.sender_id == self._my_id:
                logger.debug('Got a msg from myself:\n%r', msg)
                return self._next_main_loop_call_ts, msgs_to_send
            response_msg = self._get_response(msg)
            if response_msg:
                bencoded_response = response_msg.encode(msg.tid)
                msgs_to_send.append((bencoded_response, addr))
            maintenance_queries_to_send = self._routing_m.on_query_received(
                msg.sender_node)
            
        elif msg.type == message.RESPONSE:
            related_query = self._querier.on_response_received(msg, addr)
            if not related_query:
                # Query timed out or unrequested response
                return self._next_main_loop_call_ts, msgs_to_send
            # lookup related tasks
            if related_query.lookup_obj:
                (lookup_queries_to_send,
                 peers,
                 num_parallel_queries,
                 lookup_done
                 ) = related_query.lookup_obj.on_response_received(
                    msg, msg.sender_node)
                msgs = self._register_queries(lookup_queries_to_send)
                msgs_to_send.extend(msgs)

                if lookup_done:
                        msgs = self._announce(related_query.lookup_obj)
                        msgs_to_send.extend(msgs)
                callback_f = related_query.lookup_obj.callback_f
                if callback_f and callable(callback_f):
                    lookup_id = related_query.lookup_obj.lookup_id
                    if peers:
                        callback_f(lookup_id, peers)
                    if lookup_done:
                        callback_f(lookup_id, None)
            # maintenance related tasks
            print 'received>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><'
            maintenance_queries_to_send = \
                self._routing_m.on_response_received(
                msg.sender_node, related_query.rtt, msg.all_nodes)

        elif msg.type == message.ERROR:
            related_query = self._querier.on_error_received(msg, addr)
            if not related_query:
                # Query timed out or unrequested response
                return self._next_main_loop_call_ts, msgs_to_send
            # lookup related tasks
            if related_query.lookup_obj:
                peers = None # an error msg doesn't have peers
                (lookup_queries_to_send,
                 num_parallel_queries,
                 lookup_done
                 ) = related_query.lookup_obj.on_error_received(
                    msg, addr)
                msgs = self._register_queries(lookup_queries_to_send)
                msgs_to_send.extend(msgs)

                if lookup_done:
                    msgs = self._announce(related_query.lookup_obj)
                    msgs_to_send.extend(msgs)
                callback_f = related_query.lookup_obj.callback_f
                if callback_f and callable(callback_f):
                    lookup_id = related_query.lookup_obj.lookup_id
                    if lookup_done:
                        callback_f(lookup_id, None)
            # maintenance related tasks
            maintenance_queries_to_send = \
                self._routing_m.on_error_received(addr)

        else: # unknown type
            return self._next_main_loop_call_ts, msgs_to_send
        msgs = self._register_queries(maintenance_queries_to_send)
        msgs_to_send.extend(msgs)
        return self._next_main_loop_call_ts, msgs_to_send

    def _on_query_received(self):
        return
    def _on_response_received(self):
        return
    def _on_error_received(self):
        return
    
    
    def _get_response(self, msg):
        if msg.query == message.PING:
            return message.OutgoingPingResponse(self._my_id)
        elif msg.query == message.FIND_NODE:
            log_distance = msg.target.log_distance(self._my_id)
            rnodes = self._routing_m.get_closest_rnodes(log_distance,
                                                       NUM_NODES, False)
            return message.OutgoingFindNodeResponse(self._my_id,
                                                    rnodes)
        elif msg.query == message.GET_PEERS:
            token = self._token_m.get()
            log_distance = msg.info_hash.log_distance(self._my_id)
            rnodes = self._routing_m.get_closest_rnodes(log_distance,
                                                       NUM_NODES, False)
            peers = self._tracker.get(msg.info_hash)
            if peers:
                logger.debug('RESPONDING with PEERS:\n%r' % peers)
            return message.OutgoingGetPeersResponse(self._my_id,
                                                    token,
                                                    nodes=rnodes,
                                                    peers=peers)
        elif msg.query == message.ANNOUNCE_PEER:
            peer_addr = (msg.sender_addr[0], msg.bt_port)
            self._tracker.put(msg.info_hash, peer_addr)
            return message.OutgoingAnnouncePeerResponse(self._my_id)
        else:
            logger.debug('Invalid QUERY: %r' % (msg.query))
            #TODO: maybe send an error back?
        
    def _on_response_received(self, msg):
        pass

    def _____on_timeout(self, addr):
        related_query = self._querier.on_timeout(addr)
        if not related_query:
            return # timeout cancelled (got response/error already)
        if related_query.lookup_obj:
            (lookup_queries_to_send,
             num_parallel_queries,
             lookup_done
             ) = related_query.lookup_obj.on_timeout(related_query.dstnode)
            msgs = self._register_queries(lookup_queries_to_send)
            msgs_to_send.extend(msgs)

            callback_f = related_query.lookup_obj.callback_f
            if lookup_done and callback_f and callable(callback_f):
                msgs = self._announce(related_query.lookup_obj)
                msgs_to_send.extend(msgs)
                lookup_id = related_query.lookup_obj.lookup_id
                related_query.lookup_obj.callback_f(lookup_id, None)
        maintenance_queries_to_send = self._routing_m.on_timeout(
            related_query.dstnode)
        msgs = self._send_queries(maintenance_queries_to_send)
        msgs_to_send.extend(msgs)
        return self._next_main_loop_call_ts, msgs_to_send

    def _announce(self, lookup_obj):
        queries_to_send, announce_to_myself = lookup_obj.announce()
        return self._register_queries(queries_to_send)
        '''
        if announce_to_myself:
            self._tracker.put(lookup_obj._info_hash,
                              (self._my_node.addr[0], lookup_obj._bt_port))
        '''
        
    def _register_queries(self, queries_to_send, lookup_obj=None):
        if not queries_to_send:
            return []
        timeout_call_ts, msgs_to_send = self._querier.register_queries(
            queries_to_send)
        self._next_main_loop_call_ts = min(self._next_main_loop_call_ts,
                                           timeout_call_ts)
        print 'register', time.time(), timeout_call_ts,
        print self._next_main_loop_call_ts,
        print msgs_to_send[0]
        return msgs_to_send
                    
        
BOOTSTRAP_NODES = (
    Node(('67.215.242.138', 6881)), #router.bittorrent.com
    Node(('192.16.127.98', 7000)), #KTH node
    )
