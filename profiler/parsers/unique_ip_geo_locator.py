# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
Prints Unique IP Geo Location Information 

"""
from parser_utils import openf
import core.message as message
import GeoIP

class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

        self.unique_geo_ip_file = openf(label + '.unique_geo_ip')

        self.unique_ip_list = set()
        self.ips_per_country = {}
        self.gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
    
    def outgoing_msg(self, ts, dst_addr, msg):
        pass

    def incoming_msg(self, ts, src_addr, msg, related_query):
        ip = src_addr[0]
	if ip not in self.unique_ip_list:
            country_code = self.gi.country_code_by_addr(ip) or '--'
            self.ips_per_country[country_code] = self.ips_per_country.get(country_code, 0) + 1
            self.unique_ip_list.add(ip)
        

    def done(self):
	#print ip_list
	for country_code, num_ips in self.ips_per_country.iteritems():
            self.unique_geo_ip_file.write('%s\t%d\n' % (country_code, num_ips))

                              
