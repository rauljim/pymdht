#! /usr/bin/env python


import sys
#sys.path.append('.')
sys.path.append('../..')

from socket import inet_ntoa
import os
import time

import pcap
import dpkt

import core.message as message
from logging import DEBUG, CRITICAL
import core.logging_conf as lc
lc.setup('.', CRITICAL)

#import parsers.cdf as cdf

print '************** Check parser config *******************'


ip = '192.16.127.98'
port = 7000

conf = [
    ['0', (ip, port+10)],
    ['1', (ip, port+11)],
    ['2', (ip, port+12)],
    ['3', (ip, port+13)],
    ['4', (ip, port+14)],
    ['5', (ip, port+15)],
    ['6', (ip, port+16)],
    ['7', (ip, port+17)],
    ['8', (ip, port+18)],
    ['9', (ip, port+19)],
    ]

multiparser_mods = [
'''
   __import__('parsers.traffic_multiparser'
               ).traffic_multiparser,
    __import__('parsers.same_ip').same_ip,
    __import__('parsers.multi_rtt').multi_rtt,
'''
    __import__('parsers.multi_bootstrap_miner').multi_rtt,
    #__import__('parsers.announce').announce,
    #__import__('parsers.infohashes').infohashes,
    ]

parser_mods = [
    __import__('parsers.get_peers').get_peers,
    __import__('parsers.announce_peer').announce_peer,
    __import__('parsers.find_node').find_node,
    __import__('parsers.ping').ping,
    __import__('parsers.ip_geo_locator').ip_geo_locator,
    __import__('parsers.unique_ip_geo_locator').unique_ip_geo_locator,
'''
    __import__('parsers.lookup_parser').lookup_parser,
    __import__('parsers.maintenance_parser'
               ).maintenance_parser,
    __import__('parsers.rtt_parser').rtt_parser,
'''
    ]    
'''
cdf_files = [
    'l_time',
    'l_queries',
    'l_queries_till_peers',
    'l_time_closest',
    'l_time_auth',
    'l_num_nodes'
'''
    ]

multiparser_cdf_files = [
     't_rtt',
     ]
'''
TIMEOUT_DELAY = 2

class QueryInfo(object):

    def __init__(self, ts, dst_addr, msg):
        self.ts = ts
        self.dst_addr = dst_addr
        self.msg = msg
        self.is_lookup = msg.query == message.GET_PEERS
        


class NodeParser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr
        self.parsers = [p_mod.Parser(label, my_addr)
                        for p_mod in parser_mods]
        self.tids = {}


    def new_msg(self, ts, src_addr, dst_addr, msg):
        related_query = None
        if self.my_addr == src_addr:
            if msg.type == message.QUERY:
                self.tids[msg.tid[0]] = QueryInfo(ts, dst_addr, msg)
            for parser in self.parsers:
                parser.outgoing_msg(ts, dst_addr, msg)
        elif self.my_addr == dst_addr:
            if msg.type == message.RESPONSE:
                try:
                    related_query = self.tids[msg.tid[0]]
                except (KeyError):
                    print '%s: parser: no query for this response' % (
                        self.label)
                if related_query and ts - related_query.ts > TIMEOUT_DELAY:
                    related_query = None
                if related_query and src_addr != related_query.dst_addr:
                    if src_addr[0] != related_query.dst_addr[0]:
                        print '%s: different IP: %r != %r %f' % (
                            self.label, related_query.dst_addr, src_addr,
                            ts - related_query.ts
                            )
                    related_query = None
            for parser in self.parsers:
                parser.incoming_msg(ts, src_addr, msg, related_query)
        return related_query
    
    def done(self):
        for parser in self.parsers:
            parser.done()

class MultinodeParser(object):
 
    def __init__(self, my_ip):
        self.my_ip = my_ip
        self.parsers = [p_mod.Parser(my_ip)
                        for p_mod in multiparser_mods]


    def new_msg(self, ts, src_addr, dst_addr, msg, related_query):
        if self.my_ip == src_addr[0]:
            for parser in self.parsers:
                parser.outgoing_msg(ts, dst_addr, msg)
        if self.my_ip == dst_addr[0]:
            for parser in self.parsers:
                parser.incoming_msg(ts, src_addr, msg, related_query)
    
    def done(self):
        for parser in self.parsers:
            parser.done()

class FragmentedPacket(object):

    def __init__(self):
        #print 'reassembling IP packet ...',
        self.data = []
        self.got_header = False
        self.got_ending = False

    def reassemble(self, frame, ip_packet, ip_more_fragments, ip_offset):
        if not ip_offset:
            self.got_header = True
            self.src_port = ip_packet.udp.sport
            self.dst_port = ip_packet.udp.dport
            self.data[0:0] = [(0, ip_packet.udp.data[:])]
        else:
            i = 0
            while len(self.data) > i and ip_offset > self.data[i][0]:
                i += 1
                self.data[i:i] = [(ip_offset, frame[34:])]
                # 14 (Ehernet) + 20 (IP) = 34
        if not ip_more_fragments:
            self.got_ending = True
        if self.got_header and self.got_ending:
            data = ''.join((data[1] for data in self.data))
            #print 'reassembly DONE'
            return self.src_port, self.dst_port, data
        return None, None, None
        
class PacketReassembler(object):

    def __init__(self):
        self.got_ip6 = False
        self.f_packets = {}

    def assamble(self, frame):
        #TODO: reassamble
        eth_packet = dpkt.ethernet.Ethernet(frame)
        try:
            ip_packet = eth_packet.ip
        except (AttributeError):
            try:
                eth_packet.ip6
                if not self.got_ip6:
                    self.got_ip6 = True
                    print 'Ignoring IPv6 packets'
            except:
                print >>sys.stderr, '>>>ERROR: WRONG IP packet'
                print eth_packet
                raise
            return None, None, None
        ip_flags = ip_packet.off / 256
        ip_offset = ip_packet.off % 256
        ip_more_fragments = (ip_flags == 32)
        if ip_more_fragments or ip_offset:
            try:
                f_packet = self.f_packets[ip_packet.src + ip_packet.dst]
            except (KeyError):
                f_packet = FragmentedPacket()
                self.f_packets[ip_packet.src + ip_packet.dst] = f_packet
            src_port, dst_port, data = f_packet.reassemble(
                frame, ip_packet, ip_more_fragments, ip_offset)
            if data:
                del self.f_packets[ip_packet.src + ip_packet.dst]
        else:
            try:
                src_port = ip_packet.udp.sport
                dst_port = ip_packet.udp.dport
                data = ip_packet.udp.data
            except (AttributeError):
                print >>sys.stderr, '>>>ERROR: WRONG UDP packet'
                return None, None, None
        src_addr = (inet_ntoa(ip_packet.src), src_port)
        dst_addr = (inet_ntoa(ip_packet.dst), dst_port)
        return src_addr, dst_addr, data

        
def parse(filenames):
    start_ts = None

    assambler = PacketReassembler()
    node_parsers = [NodeParser(label, addr)
                    for label, addr in conf]
    multinode_parser = MultinodeParser(ip)
    all_parsers =  node_parsers + [multinode_parser]

    num_frames = 0
    try:
     for filename in filenames:
        print '>>>>', filename
        frames = pcap.pcap(filename)
        for num_frames, (ts_absolute, frame) in enumerate(frames): 
            if num_frames % 10000 == 0:
                print '>>>>', num_frames

            if not start_ts:
                start_ts = ts_absolute
            ts = ts_absolute - start_ts # ts relative to start
        
            try:
                src_addr, dst_addr, data = assambler.assamble(frame)
            except:
                print ts
                raise
            if not data:
                continue
            try:
                datagram = message.Datagram(data, src_addr)
                msg = message.IncomingMsg(datagram)
            except(message.MsgError):
                #print >>sys.stderr, '>>>ERROR decoding', `data`
                continue
            except(TypeError):
                print >>sys.stderr,'>>>ERROR:', data
                raise
            related_query = None
            for parser in node_parsers:
                related_query =  parser.new_msg(
                    ts, src_addr, dst_addr, msg) or related_query
            multinode_parser.new_msg(ts, src_addr, dst_addr, msg,
                                     related_query)
    except (KeyboardInterrupt):
        print 'WARNING: parsing incomplete'
    for parser in all_parsers:
        parser.done()


if __name__ == '__main__':
    
    current_dir = os.getcwd()
    try:
        os.mkdir('parser_results')
    except OSError:
   	print "Existing data in parser_results will be overwriten!!!" 
    file_prefix = os.path.basename(current_dir)[:15] + '.pcap'
    if not os.path.isfile(file_prefix):
        raise Exception, 'Capture file (%s) does not exist' % (file_prefix)
    filenames = [file_prefix]
    i = 0
    while 1:
        i += 1
        filename = '%s%d' % (file_prefix, i)
        if os.path.isfile(filename):
            filenames.append(filename)
        else:
            break
    
    print 'Parsing', filenames, '...'
    parse(filenames)
    '''	
    for filename in cdf_files:
        for label, _ in conf:
            cdf.cdf_file('parser_results/' + label + '.' + filename)
    for filename in multiparser_cdf_files:
        cdf.cdf_file('parser_results/m.' + filename)
    '''
    
class _Parser(object):
    '''Template'''

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

    def outgoing_msg(self, ts, dst_addr, msg):
        pass

    def incoming_msg(self, ts, src_addr, msg):
        pass

    def done(self):
        self.output = open(self.label + '.lookup_time', 'w')
        pass
