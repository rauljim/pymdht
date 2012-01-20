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


NUM_BITS = 160
MIN_PREFIX_BITS = 18
MAX_LOG_DISTANCE = NUM_BITS - MIN_PREFIX_BITS

NUM_PARALLEL_EXTRACTIONS = 3
EXTRACTION_DELAY = 1

class ExtractingNode(object):
    def __init__(self, lookup_node):
        self.lookup_node = lookup_node
        self.target = lookup_node.target
        self.distance_to_target = lookup_node.distance_to_target
        self.last_index =  NUM_BITS - MIN_PREFIX_BITS
        self.found_nodes = set()
        self.reachable = False
        self.last_extraction_ts = 0
        self.extraction_done = False

    def next_step_target(self):
        i = self.last_index - 1
        step_target = self.target.generate_close_id(i)
        self.last_index = i
        if i < 120:
            print '120!!!!!!!!!!'
            self.extraction_done = True
        if self.distance_to_target.log > MAX_LOG_DISTANCE:
            self.extraction_done = True
        return step_target

    def add_found_nodes(self, nodes):
        self.reachable = True
        num_duplicated = 0
        for node_ in nodes:
            if node_ in self.found_nodes:
                num_duplicated += 1
            self.found_nodes.add(node_)
        if num_duplicated == len(nodes):
            self.extraction_done = True

    def timeout_handler(self):
        self.extraction_done = True

            
class ExtractingQueue(object):
    def __init__(self, target):
        self.target = target
        self.extracting_nodes = []
        self.extracted_nodes = []
        self.unreachable_nodes = []
        self.added_nodes = set()

    def add_node(self, node_):
        if node_ in self.added_nodes:
            return
        lookup_node = LookupNode(node_, self.target)
        self.added_nodes.add(lookup_node)
        extracting_node = ExtractingNode(lookup_node)
        self.extracting_nodes.append(extracting_node)
        self.extracting_nodes.sort(key=attrgetter('distance_to_target.int'))

    def next_node_step_target(self):
        i = 0
        if (len(self.added_nodes) > 200 and self.extracting_nodes
            and self.extracting_nodes[0].distance_to_target.log > MAX_LOG_DISTANCE):
                # Closest node to target is not in range, wait a bit
                return None, None
        while i < min(NUM_PARALLEL_EXTRACTIONS, len(self.extracting_nodes)):
            extracting_node = self.extracting_nodes[i]
            if 0:#i > 10:
                if extracting_node.distance_to_target.log > MAX_LOG_DISTANCE:
                    del self.extracting_nodes[i]
                    #CAREFUL: do not increment i
                    continue
            if extracting_node.extraction_done:
                # done with this node
                self.extracted_nodes.append(extracting_node)
                del self.extracting_nodes[i]
                #CAREFUL: do not increment i
                continue
            current_time = time.time()
            if current_time > (extracting_node.last_extraction_ts
                               + EXTRACTION_DELAY):
                step_target = extracting_node.next_step_target()
                if step_target:
                    extracting_node.last_extraction_ts = current_time
                    #print extracting_node.distance_to_target.log
                    return extracting_node, step_target
            i = i + 1 # too soon or node completely extracted. Next!
        return None, None # no node to extract this round

    def in_range(self, node_, range_extension=0):
        return (node_.id.log_distance(self.target)
                < NUM_BITS - MIN_PREFIX_BITS + range_extension)

    def print_summary(self):
        num_nodes_pinged = 0
        num_nodes_pinged_r = 0
        num_inrange = 0
        num_inrange_r = 0 
        for en in self.extracted_nodes:
            num_nodes_pinged += 1
            if en.reachable:
                num_nodes_pinged_r += 1
            if self.in_range(en.lookup_node):
                num_inrange += 1
                if en.reachable:
                    num_inrange_r += 1
            
        print 'Nodes pinged (reachable):', num_nodes_pinged, num_nodes_pinged_r
        print 'Nodes inrange (reachable):', num_inrange, num_inrange_r


        i = 0
        for en in self.unreachable_nodes:
            if self.in_range(en.lookup_node):
                i+= 1
        print 'Nodes unreachable:', len(self.unreachable_nodes), i 
    
    def print_results(self):
        i = 0
        for n in self.added_nodes:
            if self.in_range(n):
                i+= 1
        print 'Total nodes:', len(self.added_nodes), i
        i = 0
        for en in self.extracting_nodes:
            if self.in_range(en.lookup_node):
                i+= 1
        print 'Nodes extracting:', len(self.extracting_nodes), i 
        i = 0
        for en in self.extracted_nodes:
            if self.in_range(en.lookup_node):
                i+= 1
        print 'Nodes extracted:', len(self.extracted_nodes), i
        i = 0
        for en in self.unreachable_nodes:
            if self.in_range(en.lookup_node):
                i+= 1
        print 'Nodes unreachable:', len(self.unreachable_nodes), i 
        i = 0
        for en in self.other_nodes:
            if self.in_range(en.lookup_node):
                i+= 1
        print 'Other nodes:', len(self.other_nodes), i
        print '-' * 40
        for extracted_node in self.extracted_nodes:
            node_ = extracted_node.node
            if node_.id.log_distance(TARGET) < NUM_BITS - NUM_PREFIX_BITS:
                print node_, node_.id.log_distance(TARGET) 

    
class Crawler(object):

    def __init__(self, bootstrap_nodes):
        self.target = RandomId()
        self.extracting_queue = ExtractingQueue(self.target)
        for node_ in bootstrap_nodes:
            self.extracting_queue.add_node(node_)
        self.my_id = self._my_id = RandomId()
        self.msg_f = message.MsgFactory(PYMDHT_VERSION, self.my_id,
                                        None)
        self.querier = Querier()
        self.last_extraction_ts = time.time()
        self.num_msgs = 0
                        
    def on_stop(self):
        pass#self._experimental_m.on_stop()

    def main_loop(self):
        current_time = time.time()
        if current_time > self.last_extraction_ts + 4:
            return #crawler DONE
        msgs_to_send = []
        extracting_node, step_target = self.extracting_queue.next_node_step_target()
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
        if datagrams_to_send:
            import sys
            sys.stdout.write('.')
            sys.stdout.flush()
        self.num_msgs += len(datagrams_to_send)
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
                related_query.experimental_obj.add_found_nodes(nodes)
                for node_ in nodes:
                    self.extracting_queue.add_node(node_)
            #else:
                #print 'not related'
        self.num_msgs += len(datagrams_to_send)
        return self.last_extraction_ts + EXTRACTION_DELAY, datagrams_to_send

    def get_bootstrap_nodes(self):
        return [en.lookup_node.node for en in self.extracting_queue.extracted_nodes[-10:]]
    
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
        task_interval=.01)
    reactor.start()
    try:
        time.sleep(2000)
    except:
        pass
        
if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    main(options, args)


