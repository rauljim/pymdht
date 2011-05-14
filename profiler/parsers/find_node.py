# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
Prints number of FIND_NODE in seconds, minutes and hours.

"""
from parser_utils import openf
import core.message as message


class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

        self.cum_find_node_file = openf(label + '.cumulative_find_node')
        self.sec_find_node_file = openf(label + '.per_sec_find_node')
        self.min_find_node_file = openf(label + '.per_min_find_node')
        self.hour_find_node_file = openf(label + '.per_hour_find_node')
        
	self.cum_find_node = 0
        self.sec_find_node = 0
        self.min_find_node = 0
	self.hour_find_node = 0
        self.current_sec = 0
        self.current_min = 0
	self.current_hour = 0
    
    def outgoing_msg(self, ts, dst_addr, msg):
        pass

    def incoming_msg(self, ts, src_addr, msg, related_query):
        int_ts = int(ts)
        if int_ts > self.current_sec:
            self.cum_find_node_file.write(
                '%d\n' % (self.cum_find_node))
            self.sec_find_node_file.write(
                '%d\n' % (self.sec_find_node))
            for i in xrange(self.current_sec + 1, int_ts):
                self.sec_find_node_file.write(
                    '%d\n' % (0))
            self.current_sec = int_ts
            self.sec_find_node = 0

	if int(int_ts / 60) > self.current_min:
            self.min_find_node_file.write(
                '%d\n' % (self.min_find_node))
	    for i in xrange(self.current_min + 1, int(int_ts / 60) ):
		self.min_find_node_file.write(
		    '%d\n' % (0))
	    self.current_min = int(self.current_sec / 60)
            self.min_find_node = 0

	if int(int_ts / 3600) > self.current_hour:
            self.hour_find_node_file.write(
                '%d\n' % (self.hour_find_node))
	    for i in xrange(self.current_hour + 1, int(int_ts / 3600) ):
		self.hour_find_node_file.write(
		    '%d\n' % (0))
	    self.current_hour = int(self.current_sec / 3600)
            self.hour_find_node = 0

        if msg.type == message.QUERY:
            if msg.query == message.FIND_NODE:
                # lookup query
                self.cum_find_node += 1
                self.sec_find_node += 1
		self.min_find_node += 1
		self.hour_find_node += 1
		pass
            else:
                # TODO: others (maintenance)
                pass

    def done(self):
        pass
                              
