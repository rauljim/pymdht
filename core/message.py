# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""
The message module contains all the data structures needed to create, encode,
and decode valid MDHT messages.

Outgoing messages are built from a few parameters. They are immutable and can
oly be stamped once.

Incoming messages are built from bencoded data. They are automatically
sanitized.

"""

import sys

import logging

import ptime as time
import bencode
from identifier import Id, ID_SIZE_BYTES, IdError
from node import Node
import message_tools as mt

private_dht_name = None

logger = logging.getLogger('dht')


NEXTSHARE_VERSION = 'NS\1\30'

# High level keys
TYPE = 'y'     # Message's type
ARGS = 'a'     # Query's arguments in a dictionary
RESPONSE = 'r' # Reply dictionary
ERROR = 'e'    # Error message string
TID = 't'      # Transaction ID
QUERY = 'q'    # Query command (only for queries)
VERSION = 'v'  # Client's version

# Valid values for key TYPE
QUERY = 'q'    # Query
RESPONSE = 'r' # Response
ERROR = 'e'    # Error

# Valid values for key QUERY
PING = 'ping'
FIND_NODE = 'find_node'
GET_PEERS = 'get_peers'
ANNOUNCE_PEER = 'announce_peer'

# Valid keys for ARGS
ID = 'id'         # Node's nodeID (all queries)
TARGET = 'target' # Target's nodeID (find_node)
INFO_HASH = 'info_hash' # Torrent's info_hash (get_peers and announce)
PORT = 'port'     # BitTorrent port (announce)
TOKEN = 'token'   # Token (announce)

# Valid keys for RESPONSE
ID = 'id'         # Node's nodeID (all replies)
NODES = 'nodes'   # String of nodes in compact format (find_nodes and get_peers)
NODES2 = 'nodes2' # Same as previous (with IPv6 support)
TOKEN = 'token'   # Token (get_peers)
PEERS = VALUES = 'values' # List of peers in compact format (get_peers)

# Valid values for ERROR
GENERIC_E = [201, 'Generic Error']
SERVER_E = [202, 'Server Error']
PROTOCOL_E = [203, 'Protocol Error']
UNKNOWN_E = [204, 'Method Unknown']

# Valid BT ports (for announcements)
MIN_BT_PORT = 1 #TODO: lower it to 1024? Let tracker decide.
MAX_BT_PORT = 2**16


class MsgError(Exception):
    """Raised anytime something goes wrong (specially when
    decoding/sanitizing).

    """


class OutgoingMsgBase(object):
    """Base class for outgoing messages. You shouldn't have instances of it.

    """

    def __init__(self, dst_node):
        self.dst_node = dst_node
        self._dict = {VERSION: NEXTSHARE_VERSION}
        if private_dht_name:
            self._dict['d'] = private_dht_name
        self._already_encoded = False
    
    def __str__(self):
        return str(self._dict)

    def __repr__(self):
        return str(self.__class__) + str(self)

    def stamp(self, tid):
        """
        Return a Datagram object ready to be sent over the network. The
        message's state is changed internally to reflect that this message has
        been stamped. This call will raise MsgError if the message has already
        been stamped.
        
        """
        
        if TID in self._dict:
            raise MsgError, 'Message has already been stamped'
        self._dict[TID] = tid
        self.sending_ts = time.time()
        return bencode.encode(self._dict)
      
class OutgoingQueryBase(OutgoingMsgBase):

    def __init__(self, dst_node, src_id):
        OutgoingMsgBase.__init__(self, dst_node)
        self._dict[TYPE] = QUERY
        self._dict[ARGS] = {ID: src_id.bin_id}
        self.lookup_obj = None
        self.experimental_obj = None
        self.got_response = False

    @property
    def query(self):
        return self._dict[QUERY]

    @property
    def tid(self):
        return self._dict[TID]

    def match_response(self, response_msg):
      """
      Return a boolean indicating whether 'response\_msg' matches this
      outgoing query. If so, as a side effect, the round trip time is
      calculated and stored in 'self.rtt'. 'self.got\_response' is set to
      True.
      
      """
      matched = self._dict[TID][0] == response_msg.tid[0]
      if matched:
          self.rtt = time.time() - self.sending_ts
          self.got_response = True            
          if response_msg.type == RESPONSE and not self.dst_node.id:
              self.dst_node.id = response_msg.src_id
      return matched

        
class OutgoingPingQuery(OutgoingQueryBase):
    
    def __init__(self, dst_node, src_id, experimental_obj=None):
        OutgoingQueryBase.__init__(self, dst_node, src_id)
        self._dict[QUERY] = PING
        self.experimental_obj = experimental_obj

        
class OutgoingFindNodeQuery(OutgoingQueryBase):

    def __init__(self, dst_node, src_id, target, lookup_obj, experimental_obj=None):
        OutgoingQueryBase.__init__(self, dst_node, src_id)
        self._dict[QUERY] = FIND_NODE
        self._dict[ARGS][TARGET] = str(target)
        self.lookup_obj = lookup_obj
        self.experimental_obj = experimental_obj


class OutgoingGetPeersQuery(OutgoingQueryBase):

    def __init__(self, dst_node, src_id, info_hash, lookup_obj, experimental_obj=None):
        OutgoingQueryBase.__init__(self, dst_node, src_id)
        self._dict[QUERY] = GET_PEERS
        self._dict[ARGS][INFO_HASH] = str(info_hash)
        self.lookup_obj = lookup_obj
        self.experimental_obj = experimental_obj

        
class OutgoingAnnouncePeerQuery(OutgoingQueryBase):
    
    def __init__(self, dst_node, src_id, info_hash, port, token):
        OutgoingQueryBase.__init__(self, dst_node, src_id)
        self._dict[QUERY] = ANNOUNCE_PEER
        self._dict[ARGS][INFO_HASH] = str(info_hash)
        self._dict[ARGS][PORT] = port
        self._dict[ARGS][TOKEN] = token

####################

class OutgoingResponseBase(OutgoingMsgBase):

    def __init__(self, dst_node, src_id):
        OutgoingMsgBase.__init__(self, dst_node)
        self._dict[TYPE] = RESPONSE
        self._dict[RESPONSE] = {ID: str(src_id)}
        
        
class OutgoingPingResponse(OutgoingResponseBase):

    def __init__(self, dst_node, src_id):
        OutgoingResponseBase.__init__(self, dst_node, src_id)


class OutgoingFindNodeResponse(OutgoingResponseBase):

    def __init__(self, dst_node, src_id, nodes):
        OutgoingResponseBase.__init__(self, dst_node, src_id)
        self._dict[RESPONSE][NODES] = mt.compact_nodes(nodes)

                          
class OutgoingGetPeersResponse(OutgoingResponseBase):

    def __init__(self, dst_node, src_id, token=None, nodes=None, peers=None):
        assert nodes or peers
        OutgoingResponseBase.__init__(self, dst_node, src_id)
        if token:
            self._dict[RESPONSE][TOKEN] = token
        if nodes:
            self._dict[RESPONSE][NODES] = mt.compact_nodes(nodes)
        if peers:
            self._dict[RESPONSE][VALUES] = mt.compact_peers(peers)

            
class OutgoingAnnouncePeerResponse(OutgoingResponseBase):
    
    def __init__(self, dst_node, src_id):
        OutgoingResponseBase.__init__(self, dst_node, src_id)

###################################

class OutgoingErrorMsg(OutgoingMsgBase):

    def __init__(self, dst_node, error):
        OutgoingMsgBase.__init__(self, dst_node)
        self._dict[TYPE] = ERROR
        self._dict[ERROR] = error

############################################

class IncomingMsg(object):
    """
    Create an object by decoding the given Datagram object. Raise 'MsgError'
    whenever the decoder fails to decode the datagram's data (e.g., invalid
    bencode).

    ?TODO: List attributes.
    """
    def __init__(self, datagram):
        bencoded_msg = datagram.data
        src_addr = datagram.addr
        self.src_addr = src_addr
        try:
            # bencode.decode may raise bencode.DecodeError
            self._msg_dict = bencode.decode(bencoded_msg)
            self._sanitize_common()
            if self.type == QUERY:
                self._sanitize_query()
            elif self.type == RESPONSE:
                self._sanitize_response()
            elif self.type == ERROR:
                self._sanitize_error()
            else:
                raise MsgError, 'Unknown TYPE value'
        except (MsgError):
            raise
        except:
            logger.warning(
                'This bencoded message is broken:\n%s' % repr(bencoded_msg)) 
            raise MsgError, 'Invalid message'

    def __repr__(self):
        return repr(self._msg_dict)

    #
    # Sanitize functions
    #
    
    def _get_value(self, k, kk=None, optional=False):
        try:
            v = self._msg_dict[k]
            if kk:
                v = v[kk]
        except (KeyError):
            if optional:
                return None
            else:
                raise MsgError, 'Non-optional key (%s:%s) not found' % (k, kk)
        except (TypeError):
            raise MsgError, 'Probably k (%r) is not a dictionary' % (k)
        return v
    
    def _get_str(self, k, kk=None, optional=False):
        v = self._get_value(k, kk, optional)
        if v is None:
            return None
        if not isinstance(v, str):
            raise MsgError, 'Value (%s:%s,%s) must be a string' % (k, kk, v)
        return v

    def _get_id(self, k, kk=None):
        try:
            v = self._get_value(k, kk)
            v = Id(v)
        except (IdError):
            raise MsgError, 'Value (%s:%s,%s) must be a valid Id' % (k, kk, v)
        return v

    def _get_int(self, k, kk=None):
        v = self._get_value(k, kk)
        try:
            v= int(v)
        except (TypeError, ValueError):
            raise MsgError, 'Value (%s:%s,%s) must be an int' % (k, kk, v)
        return v
    
    def _sanitize_common(self):
        # Make sure the decoded data is a dict and has a TID key
        try:
            self.tid = self._msg_dict[TID]
        except (TypeError):
            raise MsgError, 'decoded data is not a dictionary'
        except (KeyError): 
            raise MsgError, 'key TID not found'
        # Sanitize TID
        if not (isinstance(self.tid, str) and self.tid):
            raise MsgError, 'TID must be a non-empty binary string'

        # Sanitize TYPE
        try:
            self.type = self._msg_dict[TYPE]
        except (KeyError):
            raise MsgError, 'key TYPE not found'
        # private dht name
        if private_dht_name:
            try:
                if self._msg_dict['d'] != private_dht_name:
                    raise MsgError, 'invalid private DHT name'
            except (KeyError, TypeError):
                raise MsgError, 'invalid private DHT name'
        # version (optional)
        self.version = self._get_str(VERSION, optional=True)
        self.ns_node = self.version \
            and self.version.startswith(NEXTSHARE_VERSION[:2])
    
    def _sanitize_query(self):
        # src_id
        self.src_id = self._get_id(ARGS, ID)
        self.src_node = Node(self.src_addr, self.src_id)
        # query
        self.query = self._get_str(QUERY)
        if self.query in [GET_PEERS, ANNOUNCE_PEER]:
            # info_hash
            self.info_hash = self._get_id(ARGS, INFO_HASH)
            if self.query == ANNOUNCE_PEER:
                self.bt_port = self._get_int(ARGS, PORT)
                if not MIN_BT_PORT <= self.bt_port <= MAX_BT_PORT:
                    raise MsgError, 'announcing to %d. Out of range' % (
                        self.bt_port)
                self.token = self._get_str(ARGS, TOKEN)
        elif self.query == FIND_NODE:
            # target
            self.target = self._get_id(ARGS, TARGET)
        return
        
    def _sanitize_response(self):
        # src_id
        self.src_id = self._get_id(RESPONSE, ID)
        self.src_node = Node(self.src_addr, self.src_id)
        # all nodes
        self.all_nodes = []
        # nodes
        c_nodes = self._get_str(RESPONSE, NODES, optional=True)
        if c_nodes:
            self.nodes = mt.uncompact_nodes(c_nodes)
            self.all_nodes = self.nodes
        # nodes2
        try:
            c_nodes2 = self._msg_dict[RESPONSE][NODES2]
        except (KeyError):
            self.nodes2 = None
        else:
            self.nodes2 = mt.uncompact_nodes2(c_nodes2)
            for n in self.nodes2:
                if n not in self.all_nodes:
                    self.all_nodes.append(n)
        # token
        self.token = self._get_str(RESPONSE, TOKEN, optional=True)
        # peers
        self.peers = None
        c_peers = self._get_value(RESPONSE, PEERS, optional=True)
        if c_peers:
            self.peers = mt.uncompact_peers(c_peers)

    def _sanitize_error(self):
        try:
            self.error = [int(self._msg_dict[ERROR][0]),
                          str(self._msg_dict[ERROR][1])]
        except:
            raise MsgError, 'Invalid error message'


class Datagram(object):

    def __init__(self, data, addr):
        self.data = data
        self.addr = addr

    def __eq__(self, other):
        return (self.data == other.data and 
                self.addr == other.addr)
