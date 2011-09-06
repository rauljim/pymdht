# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
Prints the lookup time in seconds (one lookup per line).
The output is not chronologically sorted.

"""

from parser_utils import openf
import core.message as message


class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

        self.cum_l_queries_file = openf(label + '.cum_l_queries', 'w')
        self.cum_m_queries_file = openf(label + '.cum_m_queries', 'w')
        self.cum_l_queries = 0
        self.cum_m_queries = 0
        self.last_write_ts = 0

        self.sec_l_queries_file = openf(label + '.sec_l_queries', 'w')
        self.sec_m_queries_file = openf(label + '.sec_m_queries', 'w')
        self.sec_l_queries = 0
        self.sec_m_queries = 0
        self.current_sec = 0

    def outgoing_msg(self, ts, dst_addr, msg):
        int_ts = int(ts)
        if int_ts > self.current_sec:
            self.cum_l_queries_file.write(
                '%d\t%d\n' % (self.current_sec,
                              self.cum_l_queries))
            self.cum_m_queries_file.write(
                '%d\t%d\n' % (self.current_sec,
                              self.cum_m_queries))

            self.sec_l_queries_file.write(
                '%d\t%d\n' % (self.current_sec,
                              self.sec_l_queries))
            self.sec_m_queries_file.write(
                '%d\t%d\n' % (self.current_sec,
                              self.sec_m_queries))
            for i in xrange(self.current_sec + 1, int_ts):
                self.sec_l_queries_file.write(
                    '%d\t%d\n' % (i, 0))
                self.sec_m_queries_file.write(
                    '%d\t%d\n' % (i, 0))
            self.current_sec = int_ts
            self.sec_l_queries = 0
            self.sec_m_queries = 0
            
        if msg.type == message.QUERY:
            if msg.query == message.GET_PEERS:
                # lookup query
                self.cum_l_queries += 1
                self.sec_l_queries += 1
            else:
                # non-lookoup query
                self.cum_m_queries += 1
                self.sec_m_queries += 1
                
    def incoming_msg(self, ts, src_addr, msg, related_query):
        pass

    def done(self):
        pass
                              
