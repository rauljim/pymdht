# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
Prints IP Geo Location Information 

"""
from parser_utils import openf
import core.message as message
import GeoIP


class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

        self.geo_ip_file = openf(label + '.geo_ip')

        self.country_counter = {}
        self.gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
    
    def outgoing_msg(self, ts, dst_addr, msg):
        pass

    def incoming_msg(self, ts, src_addr, msg, related_query):
	country_code = self.gi.country_code_by_addr(src_addr[0])
        self.country_counter[country_code] = self.country_counter.get(country_code, 0) + 1

    def done(self):
	for country_code, num_ips in self.country_counter.iteritems():
            self.geo_ip_file.write('%s\t%d\n' % (country_code, num_ips))
