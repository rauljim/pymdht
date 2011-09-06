# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""


"""

from parser_utils import openf
import core.message as message


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
            else:
                # non-lookoup query
                self.num_m_q += 1
                
    def incoming_msg(self, ts, src_addr, msg, related_query):
        if related_query:
#                        self.num_l_wport += 1
#                        self.num_m_wport += 1
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
    
                              
