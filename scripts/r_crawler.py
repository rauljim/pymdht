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

import core.logging_conf as logging_conf
from core.identifier import Id, RandomId
import core.message as message
from core.querier import Querier
from core.message import QUERY, RESPONSE, ERROR, version_repr
from core.node import Node, LookupNode
import core.minitwisted as minitwisted

logger = logging.getLogger('dht')

PYMDHT_VERSION = (12, 2, 1)

PING = False


MIN_PREFIX_BITS = 10



NUM_BITS = 160
MAX_LOG_DISTANCE = NUM_BITS - MIN_PREFIX_BITS

NUM_PARALLEL_EXTRACTIONS = 500
EXTRACTION_DELAY = .5



class RCrawler(object):

    def __init__(self, ok_nodes, dead_nodes, fix_prefix_len, t):
        self.fix_prefix_len = fix_prefix_len
        self.t = t
        self.known_nodes = set()
        self.pending_nodes = []
        self.ok_nodes = self._split(ok_nodes)
        self.dead_nodes = self._split(dead_nodes)

        self.bootstrap_index = 0
        
        self.rcrawlers = None
        self.next_rcrawler = 0
        self.last_query_ts = 0

        self.leaf = False
        self.done = False

    def next(self):
        if self.done:
            return None, None, None
        if self.rcrawlers:
            if self.rcrawlers[self.next_rcrawler].done:
                self.next_rcrawler = self.next_rcrawler ^ 1 #round-robin
                if self.rcrawlers[self.next_rcrawler].done:
                    self.done = True
                    return None, None, None
            node_, target, rcrawler_obj = self.rcrawlers[self.next_rcrawler].next()
            self.next_rcrawler = self.next_rcrawler ^ 1 #round-robin
            return node_, target, rcrawler_obj
            
        if self.pending_nodes:
            node_ = self.pending_nodes.pop(0)
            self.last_query_ts = time.time()
            return node_, node_.id, self
        if time.time() < self.last_query_ts + 2:
            # wait for timeouts
            return None, None, None
        if self.fix_prefix_len == 20:# len(self.ok_nodes[0]) + len(self.ok_nodes[1]) < 6:
            # this is a leaf
            self.done = True
            return None, None, None

        b_node = None
        if len(self.ok_nodes[0]) < 3 or len(self.ok_nodes[1]) < 3:
            if len(self.ok_nodes[0]) < 3:
                bootstrap_gen = self.ok_nodes[1].__iter__()
            if len(self.ok_nodes[1]) < 3:
                bootstrap_gen = self.ok_nodes[0].__iter__()
            i = 0
            try:
                while i <= self.bootstrap_index:
                    i += 1
                    b_node = bootstrap_gen.next()
                self.bootstrap_index += 1
            except (StopIteration):
                print 'cross boostrap failed'
                self.leaf = True
                self.done = True
        if b_node:
            print 'cross bootstrap'
            self.last_query_ts = time.time()
            return b_node, b_node.id.generate_close_id(NUM_BITS - self.fix_prefix_len), self
        print 'R SPLIT', self.fix_prefix_len, '>', self.fix_prefix_len + 1
        self.rcrawlers = (RCrawler(
                self.ok_nodes[0], self.dead_nodes[0], self.fix_prefix_len + 1,
                self.t.set_bit(NUM_BITS - (self.fix_prefix_len + 1), 0)),
                          RCrawler(
                self.ok_nodes[1], self.dead_nodes[1], self.fix_prefix_len + 1,
                self.t.set_bit(NUM_BITS - (self.fix_prefix_len + 1), 1)))
        return None, None, None

    def got_nodes_handler(self, node_, nodes):
        if node_:
            # node_ is None on bootstrap
            self.ok_nodes[self._get_bit(node_)].add(node_)
        for n in nodes:
            if n.id.distance(self.t).prefix_len < self.fix_prefix_len:
                continue # node out of scope
            if n not in self.known_nodes:
                self.known_nodes.add(n)
                self.pending_nodes.append(n)

    def timeout_handler(self, node_):
        self.dead_nodes[self._get_bit(node_)].add(node_)

    def print_result(self):
        if self.rcrawlers:
            self.rcrawlers[0].print_result()
            self.rcrawlers[1].print_result()
        else:
            print '%3d | %3d %3d | %3d %3d' % (self.fix_prefix_len,
                                               len(self.ok_nodes[0]),
                                               len(self.dead_nodes[0]),
                                               len(self.ok_nodes[1]),
                                               len(self.dead_nodes[1]),)
            
    def get_num_ok(self):
        if self.rcrawlers:
            return self.rcrawlers[0].get_num_ok() + self.rcrawlers[1].get_num_ok()
        return len(self.ok_nodes[0]) + len(self.ok_nodes[1])

    def get_num_dead(self):
        if self.rcrawlers:
            return self.rcrawlers[0].get_num_dead() + self.rcrawlers[1].get_num_dead()
        return len(self.dead_nodes[0]) + len(self.dead_nodes[1])

    def _split(self, nodes):
        splitted_nodes = (set(), set())
        for n in nodes:
            splitted_nodes[self._get_bit(n)].add(n)
        return splitted_nodes
                               
    def _get_bit(self, node_):
        if node_.id.long & (1 << (NUM_BITS - self.fix_prefix_len - 1)):
            return 1
        else:
            return 0

        
class Crawler(object):

    def __init__(self, bootstrap_nodes):
        self.rcrawler = RCrawler(set(), set(), 13, bootstrap_nodes[0].id)
        self.rcrawler.got_nodes_handler(None, bootstrap_nodes)
        self.my_id = self._my_id = RandomId()
        self.msg_f = message.MsgFactory(PYMDHT_VERSION, self.my_id,
                                        None)
        self.querier = Querier()
        self.next_main_loop_ts = 0
        self.num_msgs = 0
        self.ok_nodes = set()
        self.dead_nodes = set()
                        
    def on_stop(self):
        pass

    def main_loop(self):
        self.next_main_loop_ts = time.time() + .1
        if self.rcrawler.done:
            print 'ind | ok dead | ok dead'
            self.rcrawler.print_result()
            print self.rcrawler.get_num_ok(), self.rcrawler.get_num_dead()
            print self.num_msgs, 'messages sent'
            for n in sorted(self.ok_nodes, key=attrgetter('ip')):
                print n
            return
        msgs_to_send = []
        node_, target, rcrawler_obj = self.rcrawler.next()
        if target:
            msg = self.msg_f.outgoing_find_node_query(
                node_,
                target,
                None,
                rcrawler_obj)
            #print 'target', `target`, 'to node', `node_.id`
            #print 'sending query to', extracting_node.node,
            #print extracting_node.node.id.log_distance(TARGET)
            msgs_to_send.append(msg)
            # Take care of timeouts
            (self._next_timeout_ts,
             timeout_queries) = self.querier.get_timeout_queries()
            for related_query in timeout_queries:
                #print 'timeout'
                related_query.experimental_obj.timeout_handler(related_query.dst_node)
                self.dead_nodes.add(related_query.dst_node)
        if msgs_to_send:
            timeout_call_ts, datagrams_to_send = self.querier.register_queries(
                msgs_to_send)
        else:
            datagrams_to_send = []
        self.num_msgs += len(datagrams_to_send)
        if datagrams_to_send and self.num_msgs % 1 == 0:
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
            return self.next_main_loop_ts, datagrams_to_send

        if msg.type == message.RESPONSE:
            related_query = self.querier.get_related_query(msg)
            #print 'got reply',
            if related_query and related_query.experimental_obj:
                #print 'related >>>>>>>>>>>>>>>>>>>>>>', len(msg.nodes)
                nodes = msg.all_nodes
                node_ = msg.src_node
                related_query.experimental_obj.got_nodes_handler(node_, nodes)
                self.ok_nodes.add(node_)
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
            print
            self.current_crawler.print_summary()
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
        task_interval=.005)
    reactor.start()
    try:
        time.sleep(20000)
    except:
        pass
        
if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    main(options, args)


