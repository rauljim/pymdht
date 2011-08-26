# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
Prints IP Geo Location Information 

"""
unique_geo_ip = {}
percentage_data = {}
for label in range(9):
	output_filename = open('/media/rizvi/git/pymdht/profiler/20110224-171415_tag/parser_results/' + str(label) + '.percentage_of_unique_ip','a')
	f1 = open('/media/rizvi/git/pymdht/profiler/20110224-171415_tag/parser_results/' + str(label) + '.geo_ip', 'r')
	f2 = open('/media/rizvi/git/pymdht/profiler/20110224-171415_tag/parser_results/' + str(label) + '.unique_geo_ip', 'r')

	#create dictionary with data from unique geo ip file........
	for line in f2:
		data = line.split()
		unique_country_code = data[0]
		unique_number_of_msg = data[1]
		unique_geo_ip[unique_country_code] = unique_number_of_msg	
	for line in f1:
        	data = line.split()
		country_code = data[0]
		number_of_msg = data[1]
		if country_code != 'None':
			value = unique_geo_ip[country_code]
			percentage = (float(value) * 100) / float(number_of_msg)
			percentage_data[country_code] = percentage
	for country_code, percentage in percentage_data.iteritems():
		output_filename.write('%s\t%.0001f\n' % (country_code, percentage))
