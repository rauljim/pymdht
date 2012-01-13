#! /usr/bin/env python


import sys
import core.ptime as time
import datetime
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
from core.node import Node
import core.minitwisted as minitwisted

logger = logging.getLogger('dht')

PYMDHT_VERSION = (12, 1, 1)

PING = False


NUM_BITS = 160
PREFIX_BITS = 18

NUM_PARALLEL_EXTRACTIONS = 50
EXTRACTION_DELAY = .01

class ExtractingNode(object):
    def __init__(self, node_, target):
        self.node = node_
        self.target = target
        self.last_index =  NUM_BITS - PREFIX_BITS
        self.found_nodes = set()
        self.reachable = False

    def next_target(self):
        if self.last_index == 0:
            return
        # if self.last_index < 130:
        #     for n in self.found_nodes:
        #         print n
        #     raise
        i = self.last_index - 1
        target = self.target.generate_close_id(i)
        self.last_index = i
        return target

    def add_found_nodes(self, nodes):
        self.reachable = True
        num_duplicated = 0
        for node_ in nodes:
            if node_ in self.found_nodes:
                num_duplicated += 1
            self.found_nodes.add(node_)
        if num_duplicated == len(nodes):
            self.last_index = 0

    def timeout_handler(self):
        self.last_index = 0

            
class ExtractingQueue(object):
    def __init__(self, target):
        self.target = target
        self.to_extract = []
        self.extracting_nodes = []
        self.extracted_nodes = []
        self.inrange_extracted_nodes = []
        self.unreachable_nodes = []
        self.added_nodes = set()
        self.other_nodes = []
        self.last_index = 0

    def add_node(self, node_):
        #print 'add',
        if node_ in self.added_nodes:
            #print 'DUPLICATED'
            return
        #print 'NEW',
        self.added_nodes.add(node_)
        extracting_node = ExtractingNode(node_, self.target)
        if not self.inrange_extracted_nodes or self.in_range(node_, 1):
            self.to_extract.append(extracting_node)
            #print 'OK'
        else:
            self.other_nodes.append(extracting_node)
            #print 'OTHER'

    def next_node_target(self):
        #print 'next_target'
        while (len(self.extracting_nodes) < NUM_PARALLEL_EXTRACTIONS
               and self.to_extract):
            #print 'pop'
            self.extracting_nodes.append(self.to_extract.pop(0))
        if not self.extracting_nodes:
            return None, None
        i = (self.last_index + 1) % len(self.extracting_nodes)
        #print len(self.extracted_nodes), len(self.to_extract), len(self.extracting_nodes), i
        extracting_node = self.extracting_nodes[i]
        if (self.in_range(extracting_node.node) or
            len(self.inrange_extracted_nodes) < 2):
            target = extracting_node.next_target()
        else:
            target = None
        if target:
            self.last_index = i
        else:
            # done with this node
            if extracting_node.reachable:
                self.extracted_nodes.append(extracting_node)
                if self.in_range(extracting_node.node):
                    self.inrange_extracted_nodes.append(extracting_node)
            else:
                self.unreachable_nodes.append(extracting_node)
            del self.extracting_nodes[i]
        return extracting_node, target


    def in_range(self, node_, range_extension=0):
        return (node_.id.log_distance(self.target)
                < NUM_BITS - PREFIX_BITS + range_extension)

    def print_summary(self):
        i = 0
        for en in self.extracted_nodes:
            if self.in_range(en.node):
                i+= 1
        print 'Nodes extracted:', len(self.extracted_nodes), i,
        i = 0
        for en in self.unreachable_nodes:
            if self.in_range(en.node):
                i+= 1
        print 'Nodes unreachable:', len(self.unreachable_nodes), i 
    
    def print_results(self):
        i = 0
        for n in self.added_nodes:
            if self.in_range(n):
                i+= 1
        print 'Total nodes:', len(self.added_nodes), i
        i = 0
        for en in self.to_extract:
            if self.in_range(en.node):
                i+= 1
        print 'Nodes to extract:', len(self.to_extract), i
        i = 0
        for en in self.extracting_nodes:
            if self.in_range(en.node):
                i+= 1
        print 'Nodes extracting:', len(self.extracting_nodes), i 
        i = 0
        for en in self.extracted_nodes:
            if self.in_range(en.node):
                i+= 1
        print 'Nodes extracted:', len(self.extracted_nodes), i
        i = 0
        for en in self.unreachable_nodes:
            if self.in_range(en.node):
                i+= 1
        print 'Nodes unreachable:', len(self.unreachable_nodes), i 
        i = 0
        for en in self.other_nodes:
            if self.in_range(en.node):
                i+= 1
        print 'Other nodes:', len(self.other_nodes), i
        print '-' * 40
        for extracted_node in self.extracted_nodes:
            node_ = extracted_node.node
            if node_.id.log_distance(TARGET) < NUM_BITS - PREFIX_BITS:
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
                        
    def on_stop(self):
        pass#self._experimental_m.on_stop()

    def main_loop(self):
        current_time = time.time()
        if current_time > self.last_extraction_ts + 4:
            return #crawler DONE
        msgs_to_send = []
        if current_time > self.last_extraction_ts + EXTRACTION_DELAY:
          extracting_node, target = self.extracting_queue.next_node_target()
          #print 'target:', `target`
          if target:
              msg = self.msg_f.outgoing_find_node_query(
                  extracting_node.node,
                  target,
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
        return current_time + EXTRACTION_DELAY, datagrams_to_send

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
        return self.last_extraction_ts + EXTRACTION_DELAY, datagrams_to_send

    def get_bootstrap_nodes(self):
        return [en.node for en in self.extracting_queue.extracted_nodes[-10:]]
    
    def print_summary(self):
        self.extracting_queue.print_summary()
    
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
        task_interval=EXTRACTION_DELAY/2)
    reactor.start()
    try:
        time.sleep(2000)
    except:
        pass
        
if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    main(options, args)


