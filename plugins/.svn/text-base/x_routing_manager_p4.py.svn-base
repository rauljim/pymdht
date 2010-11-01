# Copyright (C) 2009 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import random
import time

import logging

import identifier
import message
import node
from node import Node, RoutingNode
from routing_table_p4 import RoutingTable


logger = logging.getLogger('dht')


#TODO2: Stop expelling nodes from tables when there are many consecutive
# timeouts (and enter off-line mode)

NUM_BUCKETS = 1 #identifier.ID_SIZE_BITS + 1
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
NODES_PER_BUCKET = [20]

#REFRESH_PERIOD = 10 * 60 # 10 minutes
QUARANTINE_PERIOD = 3 * 60 # 3 minutes

MAX_NUM_TIMEOUTS = 2
#PING_DELAY_AFTER_TIMEOUT = 30 #seconds


#MIN_RNODES_BOOTSTRAP = 10
#NUM_NODES_PER_BOOTSTRAP_STEP = 5

BOOTSTRAP_MODE = 'bootstrap_mode'
#FIND_CLOSEST_MODE = 'find_closest_mode'
NORMAL_MODE = 'normal_mode'
MAINTENANCE_DELAY = {BOOTSTRAP_MODE: 1,
#                    FIND_CLOSEST_MODE: 3,
                     NORMAL_MODE: 60}

REFRESH_DELAY_FOR_NON_NS = .020 #seconds

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
#        self.last_maintenance_index = -1

        self.maintenance_mode = BOOTSTRAP_MODE
        self.lookup_mode = False
       
        self._query_received_queue = _QueryReceivedQueue(self.table)
        self._found_nodes_queue = _FoundNodesQueue(self.table)

        self.maintenance_tasks = [self._ping_a_staled_rnode,
                                  self._ping_a_query_received_node,
                                  self._ping_a_found_node]

    def notify_lookup_start(self):
        self.lookup_mode = True

    def notify_lookup_stop(self):
        self.lookup_mode = False

    
        
    def do_maintenance(self):
        if self.lookup_mode:
            # Do not send maintenance pings during lookup
            return MAINTENANCE_DELAY[self.maintenance_mode]
        
        if self.maintenance_mode == BOOTSTRAP_MODE:
            self._do_bootstrap()
#        elif self.maintenance_mode == FIND_CLOSEST_MODE:
#            self.bootstrap_lookup()
#            self.maintenance_mode = NORMAL_MODE
        else:
            for _ in range(len(self.maintenance_tasks)):
                task = self.maintenance_tasks.pop(0)
                self.maintenance_tasks.append(task)
                if task():
                    break
        return MAINTENANCE_DELAY[self.maintenance_mode]
        
    def _do_bootstrap(self):
        m_bucket, _ = self.table.buckets[0]
        if not self.bootstrap_nodes\
                or not m_bucket.there_is_room():
            # Stop bootstrap. Go normal
            self.maintenance_mode = NORMAL_MODE
            return
        index = random.randint(0,
                               len(self.bootstrap_nodes) - 1)
        self._send_maintenance_ping(self.bootstrap_nodes[index])
        del self.bootstrap_nodes[index]

    def _ping_a_staled_rnode(self):
        m_bucket, r_bucket = self.table.buckets[0]
        rnode = m_bucket.get_stalest_rnode()
        if time.time() > rnode.last_seen + QUARANTINE_PERIOD:
            print '[%f] staled rnode %d' % (
                time.time(),
                self.my_node.log_distance(rnode))
            self._send_maintenance_ping(rnode)
            return True
        return False

    def _ping_a_found_node(self):
        node_ = self._found_nodes_queue.pop(0)
        if node_:
            logger.debug('pinging node found: %r', node_)
            print '[%f] found node %d' % (
                time.time(),
                self.my_node.log_distance(node_))
            self._send_maintenance_ping(node_)
            return True
        return False

    def _ping_a_query_received_node(self):
        node_ = self._query_received_queue.pop(0)
        if node_: 
            print '[%f] query received %d' % (
                time.time(),
                self.my_node.log_distance(node_))
            self._send_maintenance_ping(node_)
            return True
        return False
                                  
    def _send_maintenance_ping(self, node_):
        m_bucket, r_bucket = self.table.buckets[0]
        if m_bucket.there_is_room() and r_bucket.there_is_room():
            target = identifier.RandomId()
            msg = message.OutgoingFindNodeQuery(self.my_node.id, target)
            m_bucket, r_bucket = self.table.buckets[0]
            print 'FIND_NODE(%d:%d:%d)' % (0,
                                           len(m_bucket),
                                           len(r_bucket)),
        else:
            print 'PING',
            msg = self.ping_msg
        if node_.id:
            m_bucket, r_bucket = self.table.buckets[0]
            print 'to %r - %d:%d:%d --' % (
                node_.addr,
                node_.log_distance(self.my_node),
                len(m_bucket),
                len(r_bucket))
        else:
            print 'to UNKNOWN id'
        self.querier.send_query(msg, node_)

        
    def on_query_received(self, node_):
        pass
            
    def on_response_received(self, node_, rtt): #TODO2:, rtt=0):
        logger.debug('on response received %d', rtt)
        m_bucket, r_bucket = self.table.buckets[0]
        rnode = m_bucket.get_rnode(node_)
        if rnode:
            # node in routing table
            self._update_rnode_on_response_received(rnode, rtt)
            return
        # The node is not in main
        rnode = r_bucket.get_rnode(node_)
        if rnode:
            # node in replacement table
            # let's see whether there is room in the main
            self._update_rnode_on_response_received(rnode, rtt)
            #TODO: leave this for the maintenance task
            if m_bucket.there_is_room(node_):
                m_bucket.add(rnode)
                self._update_rnode_on_response_received(rnode, rtt)
                r_bucket.remove(rnode)
            return
        # The node is nowhere
        # Add to main table (if the bucket is not full)
        #TODO: check wether in replacement_mode
        if m_bucket.there_is_room():
            rnode = node_.get_rnode()
            m_bucket.add(rnode)
            self._update_rnode_on_response_received(rnode, rtt)
            return
        # The main bucket is full
        # Let's see whether this node's latency is good
        highest_rtt_rnode = m_bucket.get_highest_rtt_rnode(10)
        if rtt < highest_rtt_rnode.rtt:
            # Replace high rtt node
            print 'replacing rnode (better RTT) %d' % (
                node_.log_distance(self.my_node))
            m_bucket.remove(highest_rtt_rnode)
            rnode = node_.get_rnode()
            m_bucket.add(rnode)
            self._update_rnode_on_response_received(rnode, rtt)
            return
        worst_rnode = self._worst_rnode(r_bucket.rnodes)
        # Get the worst node in replacement bucket and see whether
        # it's bad enough to be replaced by node_
        if worst_rnode \
                and worst_rnode.timeouts_in_a_row() > MAX_NUM_TIMEOUTS:
            # This node is better candidate than worst_rnode
            r_bucket.remove(worst_rnode)
            rnode = node_.get_rnode()
            r_bucket.add(rnode)
            self._update_rnode_on_response_received(rnode, rtt)
        
    def on_error_received(self, node_):
        pass
    
    def on_timeout(self, node_):
        if not node_.id:
            return # This is a bootstrap node (just addr, no id)
        m_bucket, r_bucket = self.table.buckets[0]
        rnode = m_bucket.get_rnode(node_)
        if rnode:
            # node in routing table: check whether it should be removed
            self._update_rnode_on_timeout(rnode)
            print 'refresh repl_bucket %d-%d' % (
                node_.log_distance(self.my_node),
                len(m_bucket.rnodes))
            r_rnodes_rtt_sorted = sorted(
                r_bucket.rnodes,
                lambda x,y: int(1000*(x.rtt-y.rtt)))
            for r_rnode in r_rnodes_rtt_sorted:
                self._query_received_queue.add(r_rnode)
            m_bucket.remove(rnode)
            if r_bucket.there_is_room():
                r_bucket.add(rnode)
            else:
                worst_rnode = self._worst_rnode(r_bucket.rnodes)
                if worst_rnode:
                    # Replace worst node in replacement table
                    r_bucket.remove(worst_rnode)
                    #self._refresh_replacement_bucket(replacement_bucket)
                    # We don't want to ping the node which just did timeout
                    r_bucket.add(rnode)
        # Node is not in main table
        rnode = r_bucket.get_rnode(node_)
        if rnode:
            # Node in replacement table: just update rnode
            self._update_rnode_on_timeout(rnode)
            
    def on_nodes_found(self, nodes):
        logger.debug('nodes found: %r', nodes)
        self._found_nodes_queue.add(nodes)

    def get_closest_rnodes(self, target_id, num_nodes=DEFAULT_NUM_NODES):
        return self.table.get_closest_rnodes(target_id, num_nodes)

    def get_main_rnodes(self):
        return self.table.get_main_rnodes()

    def print_stats(self):
        self.table.print_stats()

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

    def _update_rnode_on_response_received(self, rnode, rtt):
        """Register a reply from rnode.

        You should call this method when receiving a response from this rnode.

        """
        rnode.rtt = rtt
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

    def _worst_rnode(self, rnodes):
        max_num_timeouts = -1
        worst_rnode_so_far = None
        for rnode in rnodes:
            num_timeouots = rnode.timeouts_in_a_row()
            if num_timeouots >= max_num_timeouts:
                max_num_timeouts = num_timeouots
                worst_rnode_so_far = rnode
        return worst_rnode_so_far

        
class _QueryReceivedQueue(object):

    def __init__(self, table):
        self.table = table
        self._queue = []

    def add(self, node_):
        self._queue.append(node_)

    def pop(self, pos):
        while self._queue:
            node_ = self._queue.pop(pos)
            m_bucket, r_bucket = self.table.buckets[0]
            if m_bucket.there_is_room():
                return node_

class _FoundNodesQueue(object):

    def __init__(self, table):
        self.table = table
        self._queue = []
        self._recently_queued_nodes = [time.time(),
                                       set(),
                                       set()]

    def add(self, nodes):
        if time.time() > self._recently_queued_nodes[0] + 5 * 60:
            self._recently_queued_nodes = [time.time(),
                                           set(),
                                           self._recently_queued_nodes[1]]
        for node_ in nodes:
            if node_ in self._recently_queued_nodes[1] \
                    or node_ in self._recently_queued_nodes[2]:
                # This node has already been queued
                continue
            if len(self._queue) > 50:
                # Queue is already too long
                continue
            m_bucket, r_bucket = self.table.buckets[0]
            rnode = m_bucket.get_rnode(node_)
            if not rnode and m_bucket.there_is_room():
                # Not in the main: add to the queue if there is room in main
                self._queue.append(node_)
                self._recently_queued_nodes[1].add(node_)

    def pop(self, pos): 
        while self._queue:
            node_ = self._queue.pop(pos)
            m_bucket, r_bucket = self.table.buckets[0]
            rnode = m_bucket.get_rnode(node_)
            if not rnode and m_bucket.there_is_room():
                # Not in the main: return it if there is room in main
                return node_



            
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
