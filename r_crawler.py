#! /usr/bin/env python


import sys
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

PYMDHT_VERSION = (12, 1, 1)

PING = False


MIN_PREFIX_BITS = 10



NUM_BITS = 160
MAX_LOG_DISTANCE = NUM_BITS - MIN_PREFIX_BITS

NUM_PARALLEL_EXTRACTIONS = 500
EXTRACTION_DELAY = .5



class RCrawler(object):

    def __init__(self, ok_nodes, dead_nodes, bit_index):
        self.bit_index = bit_index
        self.pending_nodes = []
        self.ok_nodes = self._split(ok_nodes)
        self.dead_nodes = self._split(dead_nodes)

        
        
        self.rcrawlers = None
        self.next_rcrawler = 0
        self.last_query_ts = 0

        self.done = False

    def next(self):
        if self.done:
            return None, None
        if self.rcrawlers:
            if self.rcrawlers[self.next_rcrawler].done:
                self.next_rcrawler = self.next_rcrawler ^ 1 #round-robin
                if self.rcrawlers[self.next_rcrawler].done:
                    self.done = True
                    return None, None
            node_, target = self.rcrawlers[self.next_rcrawler].next()
            self.next_rcrawler = self.next_rcrawler ^ 1 #round-robin
            return node_, target
            
        if self.pending_nodes:
            node_ = self.pending_nodes.pop(0)
            self.last_query_ts = time.time()
            return node_, node_.id
        if time.time() < self.last_query_ts + 2:
            # wait for timeouts
            return None, None
        if len(self.ok_nodes[0]) + len(self.ok_nodes[1]) < 6:
            # this is a leaf
            self.done = True
            return None, None
        #if len(self.ok_nodes[0]) < 3:
            
        self.rcrawlers = (RCrawer(
                self.ok_nodes[0], self.dead_nodes[0], self.bit_index+1),
                          RCrawer(
                self.ok_nodes[1], self.dead_nodes[1], self.bit_index+1))
        #if not len(self.ok_nodes[0]) < 6:
            
        

    def got_nodes(self, node_, nodes):
        self.ok_nodes[self._get_bit(node_)], add(node_)
        for n in nodes:
            self.pending_nodes.append(n)

    def got_timeout(self, node_):
        self.dead_nodes[self._get_bit(node_)], add(node_)

    def _split(self, nodes):
        splitted_nodes = (set(), set())
        for n in nodes:
            splitted_nodes[self._get_bit(n)].add(n)
        return splitted_nodes
                               
    def _get_bit(self, node_):
        if n.id.int & (1 << (NUM_BITS - self.bit_index - 1)):
            return 1
        else:
            return 0

        
class Crawler(object):

    def __init__(self, bootstrap_nodes):
        self.target = RandomId()
        self.extracting_queue = ExtractingQueue(self.target)
        for node_ in bootstrap_nodes:
            is_new_node = self.extracting_queue.add_node(node_)
        self.my_id = self._my_id = RandomId()
        self.msg_f = message.MsgFactory(PYMDHT_VERSION, self.my_id,
                                        None)
        self.querier = Querier()
        self.last_extraction_ts = time.time()
        self.num_msgs = 0
        self.nodes_inrange_w_response = set()
                        
    def on_stop(self):
        pass#self._experimental_m.on_stop()

    def main_loop(self):
        current_time = time.time()
        if current_time > self.last_extraction_ts + 4:
            return #crawler DONE
        msgs_to_send = []
        only_inrange = len(self.nodes_inrange_w_response) > 4
        extracting_node, step_target = \
            self.extracting_queue.next_node_step_target(only_inrange)
        if step_target:
            msg = self.msg_f.outgoing_find_node_query(
                extracting_node.lookup_node,
                step_target,
                None,
                extracting_node)
            #print 'sending query to', extracting_node.node,
            #print extracting_node.node.id.log_distance(TARGET)
            msgs_to_send.append(msg)
            self.last_extraction_ts = current_time
            # Take care of timeouts
            (self._next_timeout_ts,
             timeout_queries) = self.querier.get_timeout_queries()
            for query in timeout_queries:
                #print 'timeout'
                query.experimental_obj.timeout_handler()
        if msgs_to_send:
            timeout_call_ts, datagrams_to_send = self.querier.register_queries(
                msgs_to_send)
        else:
            datagrams_to_send = []
        self.num_msgs += len(datagrams_to_send)
        if datagrams_to_send and self.num_msgs % 100 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
        return current_time + .01, datagrams_to_send

    def on_datagram_received(self, datagram):
        data = datagram.data
        addr = datagram.addr
        datagrams_to_send = []
        try:
            msg = self.msg_f.incoming_msg(datagram)
        except(message.MsgError):
            # ignore message
            return self.last_extraction_ts + EXTRACTION_DELAY, datagrams_to_send

        if msg.type == message.RESPONSE:
            related_query = self.querier.get_related_query(msg)
            #print 'got reply',
            if related_query and related_query.experimental_obj:
                #print 'related >>>>>>>>>>>>>>>>>>>>>>', len(msg.nodes)
                try:
                    nodes = msg.nodes
                except AttributeError:
                    print '\nno nodes>>>>>>>', msg._msg_dict
                    nodes = []
                lookup_node = related_query.dst_node
                if in_range(lookup_node):
                    self.nodes_inrange_w_response.add(lookup_node)
                related_query.experimental_obj.add_found_nodes(nodes)
                new_nodes = False
                for node_ in nodes:
                    self.extracting_queue.add_node(node_)
        self.num_msgs += len(datagrams_to_send)
        return self.last_extraction_ts + EXTRACTION_DELAY, datagrams_to_send

    def get_bootstrap_nodes(self):
        return [en.lookup_node.node for en in self.extracting_queue.pinged_nodes[-100:]]
    
    def print_summary(self):
        self.extracting_queue.print_summary()
        print "Messages sent:", self.num_msgs
    
    def print_results(self):
        self.extracting_queue.print_results()


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
    ip, port_str = args
    port = int(port_str)
    bootstrap_node = Node((ip, port), RandomId())
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


