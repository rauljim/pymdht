# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""


"""
from parser_utils import openf
import core.message as message


class Parser(object):

    def __init__(self, my_ip):
        self.my_ip = my_ip

        self.ip_rtt = {}


    def outgoing_msg(self, ts, dst_addr, msg):
        pass 
                
    def incoming_msg(self, ts, src_addr, msg, related_query):
        if related_query:
            self.ip_rtt[src_addr[0]] = src_addr[1]

    def done(self):
        self.t_rtt_file = openf('m.miner', 'w')
        for ip, port in self.ip_rtt.iteritems():
            self.t_rtt_file.write('%s %d\n' % (ip, port))

    
                              
