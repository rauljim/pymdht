# Copyright (C) 2009 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import random
import time

import logging

import identifier as identifier
import message as message
import node
from node import Node, RoutingNode
from routing_table2 import RoutingTable
from routing_tools import QueryReceivedQueue, FoundNodesQueue

logger = logging.getLogger('dht')


#TODO2: Stop expelling nodes from tables when there are many consecutive
# timeouts (and enter off-line mode)

NUM_BUCKETS = identifier.ID_SIZE_BITS + 1
"""
We need (+1) to cover all the cases. See the following table:
Index | Distance      | Comment
0     | [2^0,2^1)     | All bits equal but the least significant bit
1     | [2^1,2^2)     | All bits equal till the second least significant bit
...
158   | [2^159,2^160) | The most significant bit is equal the second is not
159   | [2^159,2^160) | The most significant bit is different
-1    | 0             | The bit strings are equal
"""

DEFAULT_NUM_NODES = 8
NODES_PER_BUCKET = [] # 16, 32, 64, 128, 256]
NODES_PER_BUCKET[:0] = [DEFAULT_NUM_NODES] \
    * (NUM_BUCKETS - len(NODES_PER_BUCKET))

REFRESH_PERIOD = 15 * 60 # 15 minutes
QUARANTINE_PERIOD = 3 * 60 # 3 minutes

MAX_NUM_TIMEOUTS = 3
PING_DELAY_AFTER_TIMEOUT = 30 #seconds


#MIN_RNODES_BOOTSTRAP = 10
#NUM_NODES_PER_BOOTSTRAP_STEP = 5

BOOTSTRAP_MODE = 'bootstrap_mode'
FIND_CLOSEST_MODE = 'find_closest_mode'
NORMAL_MODE = 'normal_mode'
MAINTENANCE_DELAY = {BOOTSTRAP_MODE: .2,
                     FIND_CLOSEST_MODE: .2,
                     NORMAL_MODE: 2}


class RoutingManager(object):
    
    def __init__(self, my_node, querier, bootstrap_lookup_f,
                 bootstrap_nodes):
        self.my_node = my_node
        self.querier = querier
        self.bootstrap_lookup = bootstrap_lookup_f
        #Copy the bootstrap list
        self.bootstrap_nodes = [n for n in bootstrap_nodes]
        
        self.table = RoutingTable(my_node, NODES_PER_BUCKET)
        self.ping_msg = message.OutgoingPingQuery(my_node.id)
        self.find_closest_msg = message.OutgoingFindNodeQuery(
            my_node.id,
            my_node.id)
        #This must be called by an external party: self.do_bootstrap()
        #After initializing callbacks

        # maintenance variables
        self.last_maintenance_index = -1

        self.maintenance_mode = BOOTSTRAP_MODE
        self.lookup_mode = False
       
        self._query_received_queue = QueryReceivedQueue(self.table)
        self._found_nodes_queue = FoundNodesQueue(self.table)

    def notify_lookup_start(self):
        self.lookup_mode = True

    def notify_lookup_stop(self):
        self.lookup_mode = False

    
        
    def do_maintenance(self):
        if self.maintenance_mode == BOOTSTRAP_MODE:
            self._do_bootstrap()
        elif self.maintenance_mode == FIND_CLOSEST_MODE:
            self.bootstrap_lookup()
            self.maintenance_mode = NORMAL_MODE
        else:
            self._ping_staled_buckets()
        return MAINTENANCE_DELAY[self.maintenance_mode]
        
    def _do_bootstrap(self):
        try:
            node = self.bootstrap_nodes.pop(0)
        except(IndexError):
            # Stop bootstrap. Now find closest nodes
            self.maintenance_mode = FIND_CLOSEST_MODE
        else:
            self._send_maintenance_ping(node)

    def _ping_staled_buckets(self):
        current_time = time.time()
        for log_distance, buckets in enumerate(self.table.buckets[:-1]):
            # Exclude last bucket (myself)
            m_bucket = buckets[0]
            if current_time < m_bucket.last_maintenance_ts + REFRESH_PERIOD:
                continue
            rnode = m_bucket.get_freshest_rnode()
            if rnode and current_time > rnode.last_seen + REFRESH_PERIOD:
                m_bucket.last_maintenance_ts = current_time
                print '[%f] staled bucket %d' % (time.time(), log_distance)
                target = self.my_node.id.generate_close_id(log_distance)
                self.bootstrap_lookup(target)
                                  
    def _send_maintenance_ping(self, node_):
        if node_.id:
            log_distance = self.table.find_next_bucket_with_room_index(node_)
        else:
            # Bootstrap nodes don't have id
            log_distance = 0
        if 0:#log_distance:
            target = self.my_node.id.generate_close_id(log_distance)
            msg = message.OutgoingFindNodeQuery(self.my_node.id, target)
            m_bucket, r_bucket = self.table.buckets[log_distance]
            print '[%f] FIND_NODE(%d:%d:%d)' % (time.time(),
                                                log_distance,
                                                len(m_bucket),
                                                len(r_bucket)),
        else:
            print '[%f] PING' % (time.time()),
            msg = self.ping_msg
        if node_.id:
            m_bucket, r_bucket = self.table.get_buckets(node_)
            print 'to (%r) %d:%d:%d --' % (
                node_.addr,
                node_.log_distance(self.my_node),
                len(m_bucket),
                len(r_bucket))
        else:
            print 'to UNKNOWN id'
        self.querier.send_query(msg, node_)

        
    def on_query_received(self, node_):
        rnode = self._on_msg_received(node_)
        if rnode:
            # node in routing table
            self._update_rnode_on_query_received(rnode)

    def on_response_received(self, node_, rtt=0): #TODO2:, rtt=0):
        logger.debug('response from %r' % (node_))
        rnode  = self._on_msg_received(node_)
        if rnode:
            # node in routing table
            self._update_rnode_on_response_received(rnode)

    def _on_msg_received(self, node_):
        m_bucket, r_bucket = self.table.get_buckets(node_)
        rnode = m_bucket.get_rnode(node_)
        if rnode:
            # The node is in the bucket (it needs to be updated)
            return rnode
        # The node is not in main
        if m_bucket.there_is_room():
            # There is room
            rnode = node_.get_rnode()
            m_bucket.add(rnode)
            return rnode
        # The main bucket is full
        bad_rnode = self._pop_bad_rnode(m_bucket)
        if bad_rnode:
            print 'replacing bad rnode...'
            # There is a bad node, add the new node
            rnode = node_.get_rnode()
            m_bucket.add(rnode)
            return rnode
        q_rnodes  = self._get_questionable_rnodes(m_bucket)
        if q_rnodes:
            print 'pinging questionable rnodes...'
            # There are questionable nodes, ping them
            rnode = node_.get_rnode()
            r_bucket.rnodes = [rnode]
            for rnode in q_rnodes:
                self._send_maintenance_ping(rnode)
            return rnode
        
    def on_error_received(self, node_):
        pass
    
    def on_timeout(self, node_):
        if not node_.id:
            return # This is a bootstrap node (just addr, no id)
        m_bucket, r_bucket = self.table.get_buckets(node_)
        rnode = m_bucket.get_rnode(node_)
        if rnode:
            # Node in routing table
            print 'timeout', rnode.addr, self.my_node.log_distance(rnode)
            self._update_rnode_on_timeout(rnode)
            if len(r_bucket):
                # There is a replacement node
                r_rnode = r_bucket.rnodes[0]
                if r_rnode.last_seen > time.time() - 60:
                    # And it is fresh
                    if rnode.timeouts_in_a_row() == 1:
                        # Give it another chance, ping it                        
                        self._send_maintenance_ping(rnode)
                    else:
                        # Several timeouts. Replace!
                        m_bucket.remove(rnode)
                        m_bucket.add(r_rnode)
                        del r_bucket.rnodes[0]
                        
            
    def on_nodes_found(self, nodes):
        return

    def get_closest_rnodes(self, target_id, num_nodes=DEFAULT_NUM_NODES):
        return self.table.get_closest_rnodes(target_id, num_nodes)

    def get_main_rnodes(self):
        return self.table.get_main_rnodes()

    def print_stats(self):
        self.table.print_stats()

    def _refresh_replacement_bucket(self, bucket):
        for rnode in bucket.rnodes:
            self._send_maintenance_ping(rnode)
        print '-----------'

    def _pop_bad_rnode(self, bucket):
        for rnode in bucket.rnodes:
            if rnode.timeouts_in_a_row() > 1:
                print 'bad rnode'
                bucket.remove(rnode)
                return rnode

    def _get_questionable_rnodes(self, bucket):
        q_nodes = []
        for rnode in bucket.rnodes:
            if time.time() > rnode.last_seen + REFRESH_PERIOD:
                print 'old>',
                q_nodes.append(rnode)
                continue
            if rnode.num_responses == 0:
                print 'no_responses',
                q_nodes.append(rnode)
        if q_nodes:
            print ''        
        return q_nodes
    
    def _worst_rnode(self, rnodes):
        max_num_timeouts = -1
        worst_rnode_so_far = None
        for rnode in rnodes:
            num_timeouots = rnode.timeouts_in_a_row()
            if num_timeouots >= max_num_timeouts:
                max_num_timeouts = num_timeouots
                worst_rnode_so_far = rnode
        return worst_rnode_so_far



    def _update_rnode_on_query_received(self, rnode):
        """Register a query from node.

        You should call this method when receiving a query from this node.

        """
        current_time = time.time()
        rnode.last_action_ts = time.time()
        rnode.msgs_since_timeout += 1
        rnode.num_queries += 1
        rnode.last_events.append((current_time, node.QUERY))
        rnode.last_events[:rnode.max_last_events]
        rnode.last_seen = current_time

    def _update_rnode_on_response_received(self, rnode, rtt=0):
        """Register a reply from rnode.

        You should call this method when receiving a response from this rnode.

        """
        current_time = time.time()
        #rnode._reset_refresh_task()
        if rnode.in_quarantine:
            rnode.in_quarantine = \
                rnode.last_action_ts < current_time - node.QUARANTINE_PERIOD
                
        rnode.last_action_ts = current_time
        rnode.num_responses += 1
        rnode.last_events.append((time.time(), node.RESPONSE))
        rnode.last_events[:rnode.max_last_events]
        rnode.last_seen = current_time

    def _update_rnode_on_timeout(self, rnode):
        """Register a timeout for this rnode.

        You should call this method when getting a timeout for this node.

        """
        rnode.last_action_ts = time.time()
        rnode.msgs_since_timeout = 0
        rnode.num_timeouts += 1
        rnode.last_events.append((time.time(), node.TIMEOUT))
        rnode.last_events[:rnode.max_last_events]
        
        
                
class RoutingManagerMock(object):

    def get_closest_rnodes(self, target_id):
        import test_const as tc
        if target_id == tc.INFO_HASH_ZERO:
            return (tc.NODES_LD_IH[155][4], 
                    tc.NODES_LD_IH[157][3],
                    tc.NODES_LD_IH[158][1],
                    tc.NODES_LD_IH[159][0],
                    tc.NODES_LD_IH[159][2],)
        else:
            return tc.NODES
