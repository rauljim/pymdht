# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
This module is the API for the whole package.

You can use the NSmdht class and its methods to interact with
the DHT.

Find usage examples in server_dht.py and interactive_dht.py.

"""

import sys

from httplib import HTTPConnection
from base64 import b64encode


#import uTorrent as ut


class Pymdht(object):
    """NSmdht is the interface for the whole package.

    Setting up the DHT is as simple as creating this object.
    The parameters are:
    - dht_addr: a tuple containing IP address and port number.
    - logs_path: a string containing the path to the log files.
    - routing_m_mod: the module implementing routing management.
    - lookup_m_mod: the module implementing lookup management.

    """
    def __init__(self, webui_addr, *args, **kwargs):
        self.host, self.port = webui_addr
        self.identity = b64encode('r:p2pnext')
             
    def stop(self):
        """Stop the DHT."""
        return
    
    def get_peers(self, _, info_hash, *args, **kwargs):
        """ Start a get peers lookup. Return a Lookup object.
        
        The info_hash must be an identifier.Id object.
        
        The callback_f must expect one parameter. When peers are
        discovered, the callback is called with a list of peers as paramenter.
        The list of peers is a list of addresses (<IPv4, port> pairs).

        The bt_port parameter is optional. When provided, ANNOUNCE messages
        will be send using the provided port number.

        """
        params = ''.join(('action=add-url&s=',
                          'magnet:?xt=urn:btih:',
                          repr(info_hash),
                          '&list=1'))
        headers = {'Authorization':  'Basic ' + self.identity}

        try:
            conn = HTTPConnection(self.host, self.port)
            conn.request('GET', '/gui/?'+params, headers=headers)
            response = conn.getresponse()
            data = response.read()
        except:
            print >>sys.stderr, 'ERROR: get_peers: %r' % (info_hash)
       
    def remove_torrent(self, info_hash):
        try:
            conn = HTTPConnection(self.host, self.port)
            conn.putrequest(r'GET', (
                    r'/gui/?action=removedata&hash='
                    + repr(info_hash)))
            conn.putheader('Authorization', 'Basic ' + self.identity)
            conn.endheaders()
            response = conn.getresponse()
            data = response.read()
        except:
            print >>sys.stderr, 'ERROR: remove_torrent: %r' % (info_hash)
