#! /usr/bin/env python

import sys
sys.path.append('..')

import core.ptime as time
import datetime
from operator import attrgetter
import os
import cPickle
import core.ptime as time
import sys, os
from optparse import OptionParser
import logging
import random

import core.logging_conf as logging_conf
from core.identifier import Id, RandomId
import core.message as message
from core.querier import Querier
from core.message import QUERY, RESPONSE, ERROR, version_repr
from core.node import Node, LookupNode
import core.minitwisted as minitwisted

logger = logging.getLogger('dht')

PYMDHT_VERSION = (12, 2, 1)

EXTRACTION_DELAY = .01

PRINT_DOT_EACH = 1

START_PREFIX_LEN = 20
LEAF_PREFIX_LEN = 22


class RCrawler(object):

    def __init__(self, target_prefix):
        self.target_prefix = target_prefix
        self.known_nodes = set()
        self.pending_nodes = set()
        self.ok_nodes = set()
        self.dead_nodes = set()
        self.num_bootstrap_attempts = 0
        self.l = len(target_prefix)
        
        self.next_rcrawler = 0
        self.last_query_ts = 0

        self.leaf = False
        self.bootstrap_done = False
        self.leaf = len(target_prefix) == LEAF_PREFIX_LEN
        if self.leaf:
            self.rcrawlers = None
        else:
            self.rcrawlers = [RCrawler(target_prefix + '0'),
                              RCrawler(target_prefix + '1')]

    def next_bootstrap_msg(self):
        dst_node = None
        target = None 
        if self.leaf:
            return dst_node, target
        self.bootstrap_done = (self.rcrawlers[0].bootstrap_done
                               and self.rcrawlers[1].bootstrap_done)
        if self.bootstrap_done:
            return dst_node, target
        for i, j in ((0,1), (1,0)):
            rcrawler0 = self.rcrawlers[i]
            rcrawler1 = self.rcrawlers[j]
            #print self.target_prefix, 'rc0 ok', len(rcrawler0.ok_nodes),
            #print 'rc1 pending', len(rcrawler1.pending_nodes),
            if (rcrawler0.ok_nodes and not rcrawler1.bootstrap_done
                and not rcrawler1.pending_nodes):
                # Try bootrapping rcrawler1 from nodes from rcrawler0
                rcrawler1.num_bootstrap_attempts += 1
                rcrawler1.bootstrap_done = rcrawler1.num_bootstrap_attempts > 2
                dst_node = random.sample(rcrawler0.ok_nodes, 1)[0]
                target =  RandomId(rcrawler1.target_prefix)
                print rcrawler1.target_prefix
                break
        if not target:
            dst_node, target = self.rcrawlers[self.next_rcrawler].next_bootstrap_msg()
            self.next_rcrawler = self.next_rcrawler ^ 1 #round-robin
        if not target:
            dst_node, target = self.rcrawlers[self.next_rcrawler].next_bootstrap_msg()
        self.bootstrap_done = (self.rcrawlers[0].bootstrap_done
                               and self.rcrawlers[1].bootstrap_done)
        return dst_node, target

    def ok_node_handler(self, node_):
        #print 'ok', self.l
        if node_:
            # node_ is None on bootstrap
            self.ok_nodes.add(node_)
            self.bootstrap_done = self.bootstrap_done or (
                self.leaf and len(self.ok_nodes) > 2)
            if self.rcrawlers:
                rcrawler_bit = node_.id.get_bit(len(self.target_prefix))
                self.rcrawlers[rcrawler_bit].ok_node_handler(node_)
            
    def timeout_handler(self, node_):
        #print 'timeout', self.l
        self.dead_nodes.add(node_)
        if self.rcrawlers:
            rcrawler_bit = node_.id.get_bit(len(self.target_prefix))
            self.rcrawlers[rcrawler_bit].timeout_handler(node_)

    def found_node_handler(self, node_):
        #print 'found', self.l
        if node_ not in self.known_nodes:
            self.known_nodes.add(node_)
            self.pending_nodes.add(node_)
            if self.rcrawlers:
                rcrawler_bit = node_.id.get_bit(len(self.target_prefix))
                self.rcrawlers[rcrawler_bit].found_node_handler(node_)

    def pinged_node_handler(self, node_):
        #print 'pinged', self.l
        try:
            self.pending_nodes.remove(node_)
        except (KeyError):
            print 'pinged a node not in pending!!!!'
        if self.rcrawlers:
            rcrawler_bit = node_.id.get_bit(len(self.target_prefix))
            self.rcrawlers[rcrawler_bit].pinged_node_handler(node_)

    def print_result(self):
        if self.rcrawlers:
            self.rcrawlers[0].print_result()
            self.rcrawlers[1].print_result()
        else:
            print '%s%s| OK: %3d, DEAD: %3d' % (
                self.target_prefix,
                ' ' * (LEAF_PREFIX_LEN - len(self.target_prefix)),
                len(self.ok_nodes), len(self.dead_nodes))
            
    def get_num_ok(self):
        if self.rcrawlers:
            return self.rcrawlers[0].get_num_ok() + self.rcrawlers[1].get_num_ok()
        return len(self.ok_nodes[0]) + len(self.ok_nodes[1])

    def get_num_dead(self):
        if self.rcrawlers:
            return self.rcrawlers[0].get_num_dead() + self.rcrawlers[1].get_num_dead()
        return len(self.dead_nodes[0]) + len(self.dead_nodes[1])


class Crawler(object):

    def __init__(self, bootstrap_nodes):
        self.target = bootstrap_nodes[0].id
        target_prefix = self.target.get_prefix(START_PREFIX_LEN)
        print target_prefix
        self.rcrawler = RCrawler(target_prefix)
        for n in bootstrap_nodes:
            self.rcrawler.found_node_handler(n)
        self.pending_nodes = bootstrap_nodes
        self.my_id = self._my_id = RandomId()
        self.msg_f = message.MsgFactory(PYMDHT_VERSION, self.my_id,
                                        None)
        self.querier = Querier()
        self.next_main_loop_ts = 0
        self.num_msgs = 0
        self.known_nodes = set(bootstrap_nodes)
        self.ok_nodes = set()
        self.dead_nodes = set()
        self.last_msg_ts = time.time()
                        
    def on_stop(self):
        pass

    def main_loop(self):
        self.next_main_loop_ts = time.time() + EXTRACTION_DELAY
        if time.time() > self.last_msg_ts + 4:# self.rcrawler.done:
            print 'ind | ok dead | ok dead'
            self.rcrawler.print_result()
            print 'total OK/DEAD', len(self.rcrawler.ok_nodes),
            print len(self.rcrawler.dead_nodes)
            print self.num_msgs, 'messages sent'
            for n in sorted(self.ok_nodes, key=attrgetter('ip')):
                print n
            return
        target = None
        msgs_to_send = []
        if ((self.num_msgs < 20 and self.num_msgs % 5 == 0)
            or (self.num_msgs < 100 and self.num_msgs % 10 == 0)
            or (self.num_msgs > 100 and self.num_msgs % 20 == 0)
            or (self.num_msgs > 100 and not self.pending_nodes)):
            dst_node, target = self.rcrawler.next_bootstrap_msg()
            if target:
                print 'O',
            else:
                print 'F',
        if not target and self.pending_nodes:
            dst_node = self.pending_nodes.pop(0)
            if dst_node.id.bin_str.startswith(self.rcrawler.target_prefix):
                self.rcrawler.pinged_node_handler(dst_node)
                target = dst_node.id
            else:
                target = self.target
            
        if target:
            msg = self.msg_f.outgoing_find_node_query(
                dst_node, target, None, self)
            #print 'target', `target`, 'to node', `node_.id`
            #print 'sending query to', extracting_node.node,
            #print extracting_node.node.id.log_distance(TARGET)
            msgs_to_send.append(msg)
            # Take care of timeouts
            (self._next_timeout_ts,
             timeout_queries) = self.querier.get_timeout_queries()
            for related_query in timeout_queries:
                #print 'timeout'
                timeout_node = related_query.dst_node
                self.dead_nodes.add(timeout_node)
                if timeout_node.id.bin_str.startswith(self.rcrawler.target_prefix):
                    self.rcrawler.timeout_handler(timeout_node)
        if msgs_to_send:
            timeout_call_ts, datagrams_to_send = self.querier.register_queries(
                msgs_to_send)
            self.last_msg_ts = time.time()
        else:
            datagrams_to_send = []
        self.num_msgs += len(datagrams_to_send)
        if datagrams_to_send and self.num_msgs % PRINT_DOT_EACH == 0:
            #print target.hex
            sys.stdout.write('.')
            sys.stdout.flush()
        return self.next_main_loop_ts, datagrams_to_send

    def on_datagram_received(self, datagram):
        data = datagram.data
        addr = datagram.addr
        try:
            msg = self.msg_f.incoming_msg(datagram)
        except(message.MsgError):
            # ignore message
            return self.next_main_loop_ts, []

        if msg.type == message.RESPONSE:
            related_query = self.querier.get_related_query(msg)
            #print 'got reply',
            if related_query and related_query.experimental_obj:
                nodes = msg.all_nodes
                src_node = msg.src_node
                print '%s >>>>>>>>>>>>>>>>>>>>>> %d' % (
                    src_node.id.hex, len(msg.nodes))
                if src_node.id.bin_str.startswith(self.rcrawler.target_prefix):
                    self.rcrawler.ok_node_handler(src_node)
                for n in nodes:
                    if n not in self.known_nodes:
                        add_node = len(self.ok_nodes) < 3
                        if n.id.bin_str.startswith(self.rcrawler.target_prefix):
                            add_node = True
                            self.rcrawler.found_node_handler(n)
                        if add_node:
                            self.known_nodes.add(n)
                            self.pending_nodes.append(n)
                self.ok_nodes.add(src_node)
        return self.next_main_loop_ts, []#datagrams_to_send

    # def get_bootstrap_nodes(self):
    #     return [en.lookup_node.node for en in self.extracting_queue.pinged_nodes[-100:]]
    
    # def print_summary(self):
    #     self.extracting_queue.print_summary()
    #     print "Messages sent:", self.num_msgs
    
    # def print_results(self):
    #     self.extracting_queue.print_results()


class MultiCrawler(object):

    def __init__(self, bootstrap_node):
        self.current_crawler = Crawler([bootstrap_node])

    def main_loop(self):
        main_loop_result = self.current_crawler.main_loop()
        if not main_loop_result:
            print 'DONE'
            #self.current_crawler.print_summary()
            bootstrap_nodes = self.current_crawler.get_bootstrap_nodes()
            self.current_crawler = Crawler(bootstrap_nodes)
            main_loop_result = self.current_crawler.main_loop()
        return main_loop_result

    def on_datagram_received(self, datagram):
        return self.current_crawler.on_datagram_received(datagram)
    
    
def main(options, args):
    id_str, v, ip, port_str = args
    id_ = Id(id_str)
    port = int(port_str)
    bootstrap_node = Node((ip, port), id_, version=v)
    mcrawler = MultiCrawler(bootstrap_node)

    logs_path = '.'# os.path.join(os.path.expanduser('~'), '.pymdht')
    logging_conf.setup(logs_path, logging.DEBUG)
    reactor = minitwisted.ThreadedReactor(
        mcrawler.main_loop, 7005, 
        mcrawler.on_datagram_received,
        task_interval=EXTRACTION_DELAY / 2)
    # NO THREADED REACTOR
    reactor._lock.acquire = lambda :None
    reactor._lock.release = lambda :None  
    reactor.run2()

        
if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    main(options, args)


