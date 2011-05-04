# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
Prints number of GET_PEERS in seconds, minutes and hours.

"""
from parser_utils import openf
import core.message as message


class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

        self.cum_gp_file = openf(label + '.cumulative_gp')
        self.sec_gp_file = openf(label + '.per_sec_gp')
        self.min_gp_file = openf(label + '.per_min_gp')
        self.hour_gp_file = openf(label + '.per_hour_gp')
        
	self.cum_gp = 0
        self.sec_gp = 0
        self.min_gp = 0
	self.hour_gp = 0
        self.current_sec = 0
        self.current_min = 0
	self.current_hour = 0
    
    def outgoing_msg(self, ts, dst_addr, msg):
        pass

    def incoming_msg(self, ts, src_addr, msg, related_query):
        int_ts = int(ts)
        if int_ts > self.current_sec:
            self.cum_gp_file.write(
                '%d\n' % (self.cum_gp))
            self.sec_gp_file.write(
                '%d\n' % (self.sec_gp))
            for i in xrange(self.current_sec + 1, int_ts):
                self.sec_gp_file.write(
                    '%d\n' % (0))
            self.current_sec = int_ts
            self.sec_gp = 0

	if int(int_ts / 60) > self.current_min:
            self.min_gp_file.write(
                '%d\n' % (self.min_gp))
	    for i in xrange(self.current_min + 1, int(int_ts / 60) ):
		self.min_gp_file.write(
		    '%d\n' % (0))
	    self.current_min = int(self.current_sec / 60)
            self.min_gp = 0

	if int(int_ts / 3600) > self.current_hour:
            self.hour_gp_file.write(
                '%d\n' % (self.hour_gp))
	    for i in xrange(self.current_hour + 1, int(int_ts / 3600) ):
		self.hour_gp_file.write(
		    '%d\n' % (0))
	    self.current_hour = int(self.current_sec / 3600)
            self.hour_gp = 0

        if msg.type == message.QUERY:
            if msg.query == message.GET_PEERS:
                # lookup query
                self.cum_gp += 1
                self.sec_gp += 1
		self.min_gp += 1
		self.hour_gp += 1
		pass
            if msg.query == message.ANNOUNCE_PEER:
                #TODO: announces
                pass
            else:
                # TODO: others (maintenance)
                pass

    def done(self):
        pass
                              
