# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
Prints Unique IP Geo Location Information 

"""
from parser_utils import openf
import core.message as message
import GeoIP
countryData = []
ip_list = []
unique_ip_list = []

class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

        self.unique_geo_ip_file = openf(label + '.unique_geo_ip')
    
    def outgoing_msg(self, ts, dst_addr, msg):
        pass

    def incoming_msg(self, ts, src_addr, msg, related_query):
	ip_list.append(src_addr[0])
    def done(self):
	#print ip_list
	unique_ip_list = list(set(ip_list))
	i = 0
	gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
	for i in range(0, len(unique_ip_list)):
		geo_info = gi.country_code_by_addr(unique_ip_list[i])
		m = 0
        	found = 0
        	for m in range(0, int(len(countryData))):
        		if countryData[m][0] == geo_info:
                          	countryData[m][1] += 1
			  	found = 1
		if found == 0:
			countryData.append([geo_info, 1])
	countryData.sort(key=lambda x:x[1], reverse = True)
	x = 0
	for x in range(0, int(len(countryData))):
		self.unique_geo_ip_file.write('%s\t%d\n' % (countryData[x][0],countryData[x][1]))
        pass
                              
