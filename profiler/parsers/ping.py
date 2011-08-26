# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
Prints number of PING in seconds, minutes and hours.

"""
from parser_utils import openf
import core.message as message


class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

        self.cum_ping_file = openf(label + '.cumulative_ping')
        self.sec_ping_file = openf(label + '.per_sec_ping')
        self.min_ping_file = openf(label + '.per_min_ping')
        self.hour_ping_file = openf(label + '.per_hour_ping')
        
	self.cum_ping = 0
        self.sec_ping = 0
        self.min_ping = 0
	self.hour_ping = 0
        self.current_sec = 0
        self.current_min = 0
	self.current_hour = 0
    
    def outgoing_msg(self, ts, dst_addr, msg):
        pass

    def incoming_msg(self, ts, src_addr, msg, related_query):
        int_ts = int(ts)
        if int_ts > self.current_sec:
            self.cum_ping_file.write(
                '%d\n' % (self.cum_ping))
            self.sec_ping_file.write(
                '%d\n' % (self.sec_ping))
            for i in xrange(self.current_sec + 1, int_ts):
                self.sec_ping_file.write(
                    '%d\n' % (0))
            self.current_sec = int_ts
            self.sec_ping = 0

	if int(int_ts / 60) > self.current_min:
            self.min_ping_file.write(
                '%d\n' % (self.min_ping))
	    for i in xrange(self.current_min + 1, int(int_ts / 60) ):
		self.min_ping_file.write(
		    '%d\n' % (0))
	    self.current_min = int(self.current_sec / 60)
            self.min_ping = 0

	if int(int_ts / 3600) > self.current_hour:
            self.hour_ping_file.write(
                '%d\n' % (self.hour_ping))
	    for i in xrange(self.current_hour + 1, int(int_ts / 3600) ):
		self.hour_ping_file.write(
		    '%d\n' % (0))
	    self.current_hour = int(self.current_sec / 3600)
            self.hour_ping = 0

        if msg.type == message.QUERY:
            if msg.query == message.PING:
                # lookup query
                self.cum_ping += 1
                self.sec_ping += 1
		self.min_ping += 1
		self.hour_ping += 1
		pass
            else:
                # TODO: others (maintenance)
                pass

    def done(self):
        pass
                              
