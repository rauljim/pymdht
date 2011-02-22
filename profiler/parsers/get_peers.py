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

        self.cum_gp_file = openf(label + '.cum_gp')
        self.cum_gp = 0
       
        self.sec_gp_file = openf(label + '.sec_gp')
        self.sec_gp = 0
        self.current_sec = 0

    def outgoing_msg(self, ts, dst_addr, msg):
        pass

    def incoming_msg(self, ts, src_addr, msg):
        int_ts = int(ts)
        if int_ts > self.current_sec:
            self.cum_gp_file.write(
                '%d\t%d\n' % (self.current_sec,
                              self.cum_gp))
            self.sec_gp_file.write(
                '%d\t%d\n' % (self.current_sec,
                              self.sec_gp))
            for i in xrange(self.current_sec + 1, int_ts):
                self.sec_gp_file.write(
                    '%d\t%d\n' % (i, 0))
                self.sec_gp_file.write(
                    '%d\t%d\n' % (i, 0))
            self.current_sec = int_ts
            self.sec_gp = 0
             
        if msg.type == message.QUERY:
            if msg.query == message.GET_PEERS:
                # lookup query
                self.cum_gp += 1
                self.sec_gp += 1
            if msg.query == message.ANNOUNCE_PEER:
                #TODO: announces
                pass
            else:
                # TODO: others (maintenance)
                pass

    def done(self):
        pass
                              
