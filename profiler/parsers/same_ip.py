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

        self.same_ip_file = openf('m.same_ip', 'w')
        
    def outgoing_msg(self, ts, dst_addr, msg):
        if self.my_ip == dst_addr[0]:
            self.same_ip_file.write('%f to %r' % (ts, dst_addr))

    def incoming_msg(self, ts, src_addr, msg, related_query):
        if self.my_ip == src_addr[0]:
            self.same_ip_file.write('%f from %r' % (ts, src_addr))

    def done(self):
        pass
