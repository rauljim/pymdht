# Copyright (C) 2010 Sara Dar
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information
import sys
import re
import operator
from socket import inet_ntoa
import string
#import pcap
#import dpkt
import binascii
import core.old_message as message

#import mainclass

class ResponseBisector:

    def __init__(self):
        return

    def all_responses(self,packetlist):
        allresponses = []
        self.firstTs= packetlist.timestamps[0]
        for i, msg in enumerate(packetlist.messages):
            if msg.type != message.RESPONSE:
                continue
            tid = packetlist.transIDs[i]
            ts = packetlist.timestamps[i]
            src_addr = packetlist.sources[i]
            dst_addr = packetlist.destinations[i]
            res = self._parse_response(msg, tid, ts, src_addr, dst_addr)
            allresponses.append(res)
        return allresponses

    def _get_nodes(self, msg):
        nodes_address = []
        nodes_ids = []

        try:
            nodes = msg.nodes or []
        except (AttributeError):
            nodes = []
        for node in nodes:
            nodes_address.append(node.addr)
            nodes_ids.append(node.id)
            
        try:
            nodes2 = msg.nodes2 or []
        except (AttributeError):
            nodes2 = []
        for node in nodes2:
            nodes_address.append(node.addr)
            nodes_ids.append(node.id)
        return nodes_address, nodes_ids


    def _parse_response(self, msg, tid, ts, src_addr, dst_addr):
        tokenval = getattr(msg, 'token', None)
        if tokenval:
            token = binascii.hexlify(tokenval)
        else:
            token = 'None'
        nodes_address, nodes_ids = self._get_nodes(msg)
        peers = getattr(msg, 'peers', None)
        hextid = binascii.hexlify(tid)
        relative_ts = round(ts - self.firstTs, 7) 
        nodes_address, nodes_ids = self._get_nodes(msg)
        resq = Responses(src_addr, dst_addr, hextid,
                             tid, relative_ts, ts,
                             msg.version, msg.type,
                             None, msg.sender_id,
                             None, nodes_address,
                             None, nodes_ids, peers,token)
        res = resq._get_data()
        return res

"""    
    def _parse_response(self, msg, tid, ts, src_addr, dst_addr):
        token = getattr(msg, 'token', None)
        nodes_address, nodes_ids = self._get_nodes(msg)
        peers = getattr(msg, 'peers', None)
        hextid = binascii.hexlify(tid)
        relative_ts = round(ts - self.firstTs, 5)      
        if token:
#FIXME: Reponses to get_peers might not have token
            response_type='get_peers' #FIXME:
            nodes_address, nodes_ids = self._get_nodes(msg)
            resq = GetPeersR(src_addr, dst_addr, hextid,
                             tid, relative_ts, ts,
                             msg.version, msg.type,
                             response_type, msg.sender_id,
                             None, nodes_address,
                             None, nodes_ids, peers)
            res = resq.get_peers_response()
        else: # no token
            if nodes_address:
                response_type='find_node' #FIXME:
                resq=FindNodeR(src_addr,dst_addr, hextid,
                               tid, relative_ts, ts,
                               msg.version,msg.type,
                               response_type, msg.sender_id,
                               nodes_address, None,
                               nodes_ids)
                res = resq.find_node_response()
            else: # no nodes
                response_type='Ping/Announce_Peer'
                resq=PingAndAnnouncePeerR(src_addr, dst_addr,
                                          hextid, tid, relative_ts, ts,
                                          msg.version, msg.type,
                                          response_type, msg.sender_id)
                res = resq.announce_peer_ping_response()
        return res
"""
                                     
class Responses:

    def __init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        response,sender,distsender,naddr,ndist,
                 nids,peers,token):

        self.src_addr=src
        self.dst_addr=dst
        self.hexaTid=hex
        self.tid=tid
        self.ts=ts
        self.absTs=absts
        self.version=ver
        self.msg_type=msg
        self.response_type=response
        self.sender_id=sender
        self.dist_from_sender=distsender
        self.nodes_address=naddr
        self.nodes_distances=ndist
        self.nodes_ids=nids
        self.peers=peers
        self.token=token

    def _get_data(self):
        return self


class GetPeersR(Responses):
    
    def __init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        response,sender,distsender,naddr,ndist,nids,peers):
        Responses.__init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        response,sender)
        self.dist_from_sender=distsender
        self.nodes_address=naddr
        self.node_distances=ndist
        self.nodes_ids=nids
        self.peers=peers

    def get_peers_response(self):        
        return self


class FindNodeR(Responses):
    
    def __init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        response,sender,naddr,ndist,nids):
        Responses.__init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        response,sender)
    
        self.nodes_address=naddr
        self.node_distances=ndist
        self.nodes_ids=nids

    def find_node_response(self):
        return self


class PingAndAnnouncePeerR(Responses):
    
    def __init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        response,sender):
        Responses.__init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        response,sender)

    def announce_peer_ping_response(self):        
        return self
