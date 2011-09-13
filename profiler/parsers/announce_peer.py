# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
Prints number of ANNOUNCE_PEER in seconds, minutes and hours.

"""
from parser_utils import openf
import core.message as message


class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

        self.cum_announce_peer_file = openf(label + '.cumulative_announce_peer')
        self.sec_announce_peer_file = openf(label + '.per_sec_announce_peer')
        self.min_announce_peer_file = openf(label + '.per_min_announce_peer')
        self.hour_announce_peer_file = openf(label + '.per_hour_announce_peer')
        
	self.cum_announce_peer = 0
        self.sec_announce_peer = 0
        self.min_announce_peer = 0
	self.hour_announce_peer = 0
        self.current_sec = 0
        self.current_min = 0
	self.current_hour = 0
    
    def outgoing_msg(self, ts, dst_addr, msg):
        pass

    def incoming_msg(self, ts, src_addr, msg, related_query):
        int_ts = int(ts)
        if int_ts > self.current_sec:
            self.cum_announce_peer_file.write(
                '%d\n' % (self.cum_announce_peer))
            self.sec_announce_peer_file.write(
                '%d\n' % (self.sec_announce_peer))
            for i in xrange(self.current_sec + 1, int_ts):
                self.sec_announce_peer_file.write(
                    '%d\n' % (0))
            self.current_sec = int_ts
            self.sec_announce_peer = 0

	if int(int_ts / 60) > self.current_min:
            self.min_announce_peer_file.write(
                '%d\n' % (self.min_announce_peer))
	    for i in xrange(self.current_min + 1, int(int_ts / 60) ):
		self.min_announce_peer_file.write(
		    '%d\n' % (0))
	    self.current_min = int(self.current_sec / 60)
            self.min_announce_peer = 0

	if int(int_ts / 3600) > self.current_hour:
            self.hour_announce_peer_file.write(
                '%d\n' % (self.hour_announce_peer))
	    for i in xrange(self.current_hour + 1, int(int_ts / 3600) ):
		self.hour_announce_peer_file.write(
		    '%d\n' % (0))
	    self.current_hour = int(self.current_sec / 3600)
            self.hour_announce_peer = 0

        if msg.type == message.QUERY:
            if msg.query == message.ANNOUNCE_PEER:
                # lookup query
                self.cum_announce_peer += 1
                self.sec_announce_peer += 1
		self.min_announce_peer += 1
		self.hour_announce_peer += 1
		pass
            else:
                # TODO: others (maintenance)
                pass

    def done(self):
        pass
                              
