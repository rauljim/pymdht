# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
Prints the lookup time in seconds (one lookup per line).
The output is not chronologically sorted.

"""
from parser_utils import openf
import core.message as message


class QueryInfo(object):

    def __init__(self, ts, dst_addr, is_lookup):
        self.ts = ts
        self.dst_addr = dst_addr
        self.is_lookup = is_lookup

class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

        self.num_l_q = 0
        self.num_m_q = 0
        self.num_l_r = 0
        self.num_m_r = 0

        self.num_l_wport = 0
        self.num_m_wport = 0
        
        self.l_rtt_file = openf(label + '.l_rtt', 'w')
        self.m_rtt_file = openf(label + '.m_rtt', 'w')
        self.t_rtt_file = openf(label + '.t_rtt', 'w')

        self.tids = {}

    def outgoing_msg(self, ts, dst_addr, msg):
            
        if msg.type == message.QUERY:
            if msg.query == message.GET_PEERS:
                # lookup query
                self.num_l_q += 1
                self.tids[msg.tid[0]] = query = QueryInfo(ts, dst_addr, True)
            else:
                # non-lookoup query
                self.num_m_q += 1
                self.tids[msg.tid[0]] = QueryInfo(ts, dst_addr, False)
                
    def incoming_msg(self, ts, src_addr, msg):
        if msg.type == message.RESPONSE:
            try:
                related_query = self.tids[msg.tid[0]]
            except (KeyError):
                print '%s: rtt_parser: no query for this response' % (
                    self.label)
                return
            if src_addr != related_query.dst_addr:
                if src_addr[0] != related_query.dst_addr[0]:
                    print '%s: rtt_parser: different IP: %r != %r %f' % (
                        self.label, related_query.dst_addr, src_addr,
                        ts - related_query.ts
                        )
                else:
                    del self.tids[msg.tid[0]]
                    if related_query.is_lookup:
                        self.num_l_wport += 1
                    else:
                        self.num_m_wport += 1
                return
            
            # addr and tid matched
            if related_query.is_lookup:
                self.num_l_r += 1
                self.l_rtt_file.write('%f\n' % (ts - related_query.ts))
            else:
                self.num_m_r += 1
                self.m_rtt_file.write('%f\n' % (ts - related_query.ts))
            self.t_rtt_file.write('%r\t%f\n' % (src_addr[0], ts - related_query.ts))

    def done(self):
        self.l_q_r_wp_file = openf(self.label + '.l_q_r_wp', 'w')
        self.l_q_r_wp_file.write('%d\t%d\t%d\n' % (
                self.num_l_q, self.num_l_r, self.num_l_wport))
        self.m_q_r_wp_file = openf(self.label + '.m_q_r_wp', 'w') 
        self.m_q_r_wp_file.write('%d\t%d\t%d\n' % (
                self.num_m_q, self.num_m_r, self.num_m_wport))
    
                              
