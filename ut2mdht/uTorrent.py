#!/usr/bin/env python
# -*- coding: utf-8 -*-

#	uTorrent.py version 0.1.1 ALPHA
#	Copyright (C) 2006-2010 Rob Crowther <weilawei@gmail.com>
#
#	This library is free software; you can redistribute it and/or modify
# 	it under the terms of the GNU Lesser General Public License as
#	published by the Free Software Foundation; either version 2.1 of the
#	License, or (at your option) any later version.
#
#	This library is distributed in the hope that it will be useful, but
#	WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#	Lesser General Public License for more details.
#
#	You should have received a copy of the GNU Lesser General Public 
#	License along with this library; if not, write to the Free Software 
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import logging, sys, socket
from base64 import b64encode
from httplib import *
from urllib import quote

#	date/timestamp [LEVEL] error message
logging.basicConfig(datefmt='%d %b %Y %H:%M:%S',
					format='%(asctime)s [%(levelname)s] %(message)s',
					filename='uTorrent.log')

#	UTORRENT CONSTANTS
#	modify these, fuck things up
UT_DEBUG					= True

#	file priorities
UT_FILE_PRIO_SKIP 				= r'0'
UT_FILE_PRIO_LOW 				= r'1'
UT_FILE_PRIO_NORMAL 			= r'2'
UT_FILE_PRIO_HIGH 				= r'3'

#	torrent states
UT_TORRENT_STATE_START			= 0x00
UT_TORRENT_STATE_FORCESTART		= 0x01
UT_TORRENT_STATE_PAUSE      	= 0x02
UT_TORRENT_STATE_STOP       	= 0x03

#	individual torrent properties
UT_TORRENT_DETAIL_HASH 			= 0
UT_TORRENT_DETAIL_TRACKERS 		= 1
UT_TORRENT_DETAIL_ULRATE 		= 2
UT_TORRENT_DETAIL_DLRATE 		= 3
UT_TORRENT_DETAIL_SUPERSEED 	= 4
UT_TORRENT_DETAIL_DHT 			= 5
UT_TORRENT_DETAIL_PEX 			= 6
UT_TORRENT_DETAIL_SEED_OVERRIDE	= 7
UT_TORRENT_DETAIL_SEED_RATIO 	= 8
UT_TORRENT_DETAIL_SEED_TIME 	= 9
UT_TORRENT_DETAIL_ULSLOTS 		= 10


#	torrent info/stats
UT_TORRENT_PROP_HASH        	= 0
UT_TORRENT_PROP_NAME        	= 2
UT_TORRENT_PROP_LABEL			= 11
UT_TORRENT_PROP_STATE			= 1
UT_TORRENT_STAT_BYTES_SIZE		= 3
UT_TORRENT_STAT_BYTES_LEFT		= 18
UT_TORRENT_STAT_BYTES_RECV		= 5
UT_TORRENT_STAT_BYTES_SENT		= 6
UT_TORRENT_STAT_SPEED_UP    	= 8
UT_TORRENT_STAT_SPEED_DOWN 		= 9
UT_TORRENT_STAT_P1000_DONE		= 4
UT_TORRENT_STAT_ETA				= 10
UT_TORRENT_STAT_AVAILABLE		= 16
UT_TORRENT_STAT_QUEUE_POS		= 17
UT_TORRENT_STAT_RATIO			= 7
UT_TORRENT_STAT_SEED_AVAIL		= 15
UT_TORRENT_STAT_PEER_AVAIL  	= 13
UT_TORRENT_STAT_SEED_CONN		= 14
UT_TORRENT_STAT_PEER_CONN		= 12

#	uTorrent
#
#	Provides a handle with fine grained torrent state
#	and file priority methods

class uTorrent(HTTPConnection):
	username = None
	password = None
	identity = None

	#	will be happy as long as you feed it valid uTorrent WebUI details
	def __init__(self, host='localhost', port='8080', username='default', password='default'):
		try:
			HTTPConnection.__init__(self, host, port)
			self.connect()
		except socket.error, exception:
			logging.critical(exception.args[1])
			logging.shutdown()
			sys.exit(1)

		self.username = username
		self.password = password

	#	creates an HTTP Basic Authentication token
	def webui_identity(self):
		if (self.identity is None):
			self.identity = self.username + ':' + self.password
			self.identity = b64encode(self.identity)

		return self.identity

	#	creates and fires off an HTTP request
	#	all webui_ methods return a python object
	def webui_action(self, selector, method=r'GET', headers=None, data=None):
		self.putrequest(method, selector)
		self.putheader('Authorization', 'Basic ' + self.webui_identity())

		if (headers is not None):
  			for (name, value) in headers.items():
  				self.putheader(name, value)

		self.endheaders()

		if (method == r'POST'):
			self.send(str(data))
			
		webui_response = self.getresponse()

		if (webui_response.status == 401):
			logging.error('401 Unauthorized Access')

			return None

		return webui_response.read()

	#	gets torrent properties
	def webui_get_props(self, torrent_hash):
		return self.webui_action(r'/gui/?action=getprops&hash=' + torrent_hash)['props']
		
	#	sets torrent properties
	def webui_set_prop(self, torrent_hash, setting, value):
		setting = quote(setting)
		value 	= quote(value)

		return self.webui_action(r'/gui/?action=setsetting&s=' + setting + r'&v=' + value + r'&hash=' + torrent_hash)

	#	sets a uTorrent setting
	def webui_set(self, setting, value):
		setting = quote(setting)
		value 	= quote(value)

		return self.webui_action(r'/gui/?action=setsetting&s=' + setting + r'&v=' + value)

	#	gets uTorrent settings
	def webui_get(self):
		return self.webui_action(r'/gui/?action=getsettings')['settings']

	#	adds a torrent via url
	#	you need to check webui_ls() again *after* you get this result
	#	otherwise, the torrent might not show up and you won't know
	#	if it was successfully added.
	def webui_add_url(self, torrent_url):
		return self.webui_action(r'/gui/?action=add-url&s=' + quote(torrent_url) + r'&list=1')

	#	adds a torrent via POST
	def webui_add_file(self, torrent_file):
		CRLF 		= '\r\n'
		method 		= r'POST'
		boundary 	= r'---------------------------22385145923439'
		headers 	= {r'Content-Type': r'multipart/form-data; boundary=' + boundary}
		data		= ''

		try:
			torrent	= open(torrent_file, 'rb')
			torrent	= torrent.read()
		except IOError:
			logging.error('Torrent I/O Error')

			return None

		data += "--%s%s" % (boundary, CRLF)
		data += "Content-Disposition: form-data; name=\"torrent_file\"; filename=\"%s\"%s" % (torrent_file, CRLF)
		data += "Content-Type: application/x-bittorrent%s" % CRLF
		data += "%s" % CRLF
		data += torrent + CRLF
		data += "--%s--%s" % (boundary, CRLF)

		headers['Content-Length'] = str(len(data))

		return self.webui_action(r'/gui/?action=add-file', method=method, headers=headers, data=data)

	#	removes a torrent
	def webui_remove(self, torrent_hash):
		return self.webui_action(r'/gui/?action=remove&hash=' + torrent_hash)
		
	#	removes a torrent and data
	def webui_remove_data(self, torrent_hash):
		return self.webui_action(r'/gui/?action=removedata&hash=' + torrent_hash)

	#	returns a giant listing of uTorrentness
	def webui_ls(self):
		return self.webui_action(r'/gui/?list=1')['torrents']

	#	returns a giant listing of uTorrentness files for a given torrent
	def webui_ls_files(self, torrent_hash):
		return self.webui_action(r'/gui/?action=getfiles&hash=' + torrent_hash)

	#	starts a torrent
	def webui_start_torrent(self, torrent_hash):
		return self.webui_action(r'/gui/?action=start&hash=' + torrent_hash + r'&list=1')

	#	force starts a torrent
	#	don't ever do this. please. this is for the sake of completeness.
	def webui_forcestart_torrent(self, torrent_hash):
		return self.webui_action(r'/gui/?action=forcestart&hash=' + torrent_hash + r'&list=1')

	#	pause a torrent
	def webui_pause_torrent(self, torrent_hash):
		return self.webui_action(r'/gui/?action=pause&hash=' + torrent_hash + r'&list=1')

	#	stop a torrent
	def webui_stop_torrent(self, torrent_hash):
		return self.webui_action(r'/gui/?action=stop&hash=' + torrent_hash + r'&list=1')

	#	set priority on a list of files
	def webui_prio_file(self, torrent_hash, torrent_files, torrent_file_prio):
		webui_cmd_prio = r'/gui/?action=setprio&hash='
		webui_cmd_prio += torrent_hash
		webui_cmd_prio += r'&p='
		webui_cmd_prio += torrent_file_prio

		for torrent_file_idx in torrent_files:
			webui_cmd_prio += r'&f='
			webui_cmd_prio += torrent_file_idx

		return self.webui_action(webui_cmd_prio)

	#	returns a dictionary of torrent names and hashes
	def uls_torrents(self):
		raw_torrent_list = self.webui_ls()
		torrent_list	 = {}

		for torrent in raw_torrent_list:
			torrent_list[torrent[UT_TORRENT_PROP_NAME]] = torrent[UT_TORRENT_PROP_HASH]

		return torrent_list

	#	returns a dictionary of file names mapping tuples of indices and parent torrent hashes
	#	ex. {'fileb.txt': (1, IAMABIGASSHASHFORATORRENT), 'filea.dat': (0, IAMABIGASSHASHFORATORRENT)}
	def uls_files(self, torrent_name=None, torrent_hash=None):
		if ((torrent_name is None) and (torrent_hash is None)):
			logging.error('Specify torrent_name or torrent_hash')

			return None

		#	faster, will use this if possible
		if (torrent_hash is not None):
			raw_file_list = self.webui_ls_files(torrent_hash)['files'][1:]

		#	slow since we need to look up the hash
		else:
			torrent_hash  = self.uls_torrents()[torrent_name]
			raw_file_list = self.webui_ls_files(torrent_hash)['files'][1:]

		file_list	 = {}
		i			 = 0

		for filename in raw_file_list[0]:
			file_list[filename[0]] = (i, torrent_hash)

			i += 1

		return file_list

	#	sets the current state of a list of torrents
	def uset_torrents_state(self, torrent_state, torrent_list_name=None, torrent_list_hash=None):
		if ((torrent_list_name is None) and (torrent_list_hash is None)):
			logging.error('Specify torrent_list_name or torrent_list_hash')
			
			return None

		if (torrent_list_hash is None):
			current_torrents = self.uls_torrents()

		if (torrent_state == UT_TORRENT_STATE_STOP):
			if (torrent_list_hash is not None):
				for torrent in torrent_list_hash:
					self.webui_stop_torrent(torrent)
			else:
				for torrent in torrent_list_name:
					self.webui_stop_torrent(current_torrents[torrent])

			return True

		elif (torrent_state == UT_TORRENT_STATE_START):
			if (torrent_list_hash is not None):
				for torrent in torrent_list_hash:
					self.webui_start_torrent(torrent)
			
			else:
				for torrent in torrent_list_name:
					self.webui_start_torrent(current_torrents[torrent])

			return True

		elif (torrent_state == UT_TORRENT_STATE_PAUSE):
			if (torrent_list_hash is not None):
				for torrent in torrent_list_hash:
					self.webui_pause_torrent(torrent)
			
			else:
				for torrent in torrent_list_name:
					self.webui_pause_torrent(current_torrents[torrent])

			return True

		elif (torrent_state == UT_TORRENT_STATE_FORCESTART):
			if (torrent_list_hash is not None):
				for torrent in torrent_list_hash:
					self.webui_forcestart_torrent(torrent)
			
			else:
				for torrent in torrent_list_name:
					self.webui_forcestart_torrent(current_torrents[torrent])

			return True

		else:
			return False

	#	sets the current priority of a list of files
	def uprio_files(self, file_list, file_prio, torrent_name=None, torrent_hash=None):
		if ((torrent_name is None) and (torrent_hash is None)):
			logging.error('Specify torrent_name or torrent_hash')
			
			return None

		#	whee, faster
		if (torrent_hash is not None):
			current_files = self.uls_files(torrent_hash=torrent_hash)

		#	slow since we need to look up the hash
		else:
			torrent_list 	= self.uls_torrents()
			current_files 	= self.uls_files(torrent_name=torrent_name)

		file_idx_list	= []

		for filename in file_list:
			file_idx_list.append(str(current_files[filename][0]))

		#	whee, faster
		if (torrent_hash is not None):
			for filename in file_list:
				self.webui_prio_file(torrent_hash, file_idx_list, file_prio)
				
		#	ew, slower
		else:
			for filename in file_list:
				self.webui_prio_file(torrent_list[torrent_name], file_idx_list, file_prio)

#	the sandbox
#   TODO: make this an interactive prompt
if (__name__ == '__main__'):
    #from code import interact
    #interact()
    
    torrent_url = "magnet:?xt=urn:btih:178b43d3072f578be87b973650bc5ab863efb268"
    
    uTorrent_handle = uTorrent(host = '192.16.125.243', port='46155', username='r',
			       password='p2pnext')
    
    uTorrent_handle.webui_add_url(torrent_url)
    import time
    print 'sleeping'
    time.sleep(10)
    
    uTorrent_handle.webui_remove_data("178b43d3072f578be87b973650bc5ab863efb268")
