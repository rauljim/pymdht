# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
Prints percentage of nodes send GET_PEERS but don't sent ANNOUNCE_PEER.

"""
from parser_utils import openf
import core.message as message
import os.path

class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

        self.get_peer_announce_peer_file = openf(label + 
					'.get_peer_announce_peer')
        
    def outgoing_msg(self, ts, dst_addr, msg):
        pass

    def incoming_msg(self, ts, src_addr, msg, related_query):
        #int_ts = int(ts)
	
        if msg.type == message.QUERY:
            if msg.query == message.GET_PEERS:
   		self.get_peer_announce_peer_file.write(
			'%s%s%s%s%s%s%s%s%s\n' % (ts,';',
						'0',';',
						src_addr,';',
						'get_peers',';',
						'null'))


        if msg.type == message.QUERY:
            if msg.query == message.ANNOUNCE_PEER:
	      if not os.path.exists(os.path.join(os.getcwd(),'/../parser_results/',
					self.label,'.get_peer_announce_peer')):	
		open(os.getcwd() + '/parser_results/' + 'self.label' + 
					'.get_peer_announce_peer','w').close()

              #self.get_peer_announce_peer_file_read = open(os.getcwd() + 
	#				'/parser_results/' + 'self.label' + 
	#				'.get_peer_announce_peer')
    	      
	      '''for line in self.get_peer_announce_peer_file_read:
		    if src_addr in line:
		       line.replace('0',ts)
		       line.replace('null','announce_peer')		
   		       self.get_peer_announce_peer_file.write(line + "\n")
		       #self.get_peer_announce_peer_file.close
		    else:'''

   		       #self.get_peer_announce_peer_file.write(
   	      self.get_peer_announce_peer_file.write(
			'%s%s%s%s%s%s%s%s%s\n' % ('0',';',
						ts,';',
						src_addr,';',
						'null',';',
						'announce_peer'))

						
    def done(self):
        pass
