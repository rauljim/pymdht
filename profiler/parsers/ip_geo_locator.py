# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
Prints IP Geo Location Information 

"""
from parser_utils import openf
import core.message as message
import GeoIP
countryData = []        

class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

        self.geo_ip_file = openf(label + '.geo_ip')
    
    def outgoing_msg(self, ts, dst_addr, msg):
        pass

    def incoming_msg(self, ts, src_addr, msg):
	gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
	geo_info = gi.country_code_by_addr(src_addr[0])
	#countryData.append(geo_info)
        #self.geo_ip_file.write('%s\n' % countryData)
        #self.geo_ip_file.write('%s\n' % geo_info)
	m = 0
        found = 0
        for m in range(0, int(len(countryData))):
        	if countryData[m][0] == geo_info:
                          countryData[m][1] += 1
			  found = 1
	if found == 0:
		countryData.append([geo_info, 1])
    def done(self):
	x = 0
	for x in range(0, int(len(countryData))):
		#self.geo_ip_file.write('%s\t%d\n' % countryData[x][0],countryData[x][1])
		self.geo_ip_file.write('%s\t%d\n' % (countryData[x][0],countryData[x][1]))
        pass
                              
