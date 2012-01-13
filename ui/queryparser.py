# Copyright (C) 2010 Sara Dar
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information
import sys
from socket import inet_ntoa
import string
#import pcap
#import dpkt
import binascii
from StringIO import StringIO
import core.old_message as message
import os
import stat
import core.identifier as identifier
import keyword

import filereader as fread

#import mainclass

class QueriesBisector:
    fname=''
    def __init__(self):
        #self.fname=filename
        self.firstTs=0


    def all_queries(self,packetlist):
         allqueries=[]
         counter=0
      
         hextid=''
         ts=''
         distance=0

         msglist=packetlist.messages
         tidlist=packetlist.transIDs
         tslist=packetlist.timestamps
         srclist=packetlist.sources
         dstlist=packetlist.destinations
         self.firstTs=tslist[0]
         for i in xrange(len(msglist)):
             msg=msglist[i]
             if msg.type == message.QUERY:
                 counter=counter+1
                 #qr.tid= tidlist[i]
                 hextid=binascii.hexlify(tidlist[i])
                 #qr.hexaTid=hextid
                 #absTs=tslist[i]
                 ts=round((tslist[i]-self.firstTs),7)
   
                 if msg.query == message.GET_PEERS:
                    
                     distance=msg.info_hash.log_distance(msg.sender_id)
                     #qr.dist_from_sender=distance
                     #qr.infohash=msg.info_hash
                     qr=GetPeers(srclist[i],dstlist[i],hextid,
                                 tidlist[i],ts,tslist[i],
                                 msg.version,msg.type,
                                 msg.query,msg.sender_id,
                                 msg.info_hash,distance)

                     query=qr.get_peers_query()
                     allqueries.append(query)
                     
                 elif msg.query == message.FIND_NODE:

                     qr=FindNode(srclist[i],dstlist[i],hextid,
                                 tidlist[i],ts,tslist[i],
                                 msg.version,msg.type,
                                 msg.query,msg.sender_id,
                                 msg.target)
                     query=qr.find_node_query()
                     allqueries.append(query)
                     #print allqueries[0].src_addr
                 elif msg.query == message.PING:
                     
                     qr=Ping(srclist[i],dstlist[i],hextid,
                                 tidlist[i],ts,tslist[i],
                                 msg.version,msg.type,
                                 msg.query,msg.sender_id)
                     query =qr.ping_query()
                     allqueries.append(query)

                 elif msg.query == message.ANNOUNCE_PEER:
                     dist=msg.info_hash.log_distance(msg.sender_id)
                     token = binascii.hexlify(msg.token)
                     qr=AnnouncePeer(srclist[i],dstlist[i],hextid,
                                 tidlist[i],ts,tslist[i],
                                 msg.version,msg.type,
                                 msg.query,msg.sender_id,
                                 msg.info_hash,msg.bt_port,
                                 token,dist)
                     query=qr.announce_peer_query()
                     allqueries.append(query)

    
         return allqueries
          
#add fake data to check for ip and id aliasing
"""
         senderid1=identifier.Id('e69ab7daffe1b89b39b74deafab06adc6270a51e')
         qr=GetPeers(('79.112.92.98',2223),('192.16.125.242',7778),'c430000',
                                 '','1.4223400','1266509210.20',
                                 msg.version,msg.type,
                                 'get_peers',senderid1,
                                 '','140')         
         query=qr.get_peers_query()
         allqueries.append(query)
         senderid2=identifier.Id('ef0581e695c69df4090110fc3e9b9117929ad7c1')
         qr=GetPeers(('24.8.65.85',47583),('192.16.125.242',7778),'a630000',
                                 '','1.4223400','1266509210.20',
                                 msg.version,msg.type,
                                 'get_peers',senderid2,
                                 '','140')         
         query=qr.get_peers_query()
         allqueries.append(query)

"""
       #  return allqueries


  

   
class Queries:

    def __init__(self,src,dst,hex,tid,ts,absts,ver,msg,query,sender):
        self.src_addr=src
        self.dst_addr=dst
        self.hexaTid=hex
        self.tid=tid
        self.ts=ts
        self.absTs=absts
        self.version=ver
        self.msg_type=msg
        self.query_type=query
        self.sender_id=sender

    def get_common_data(self):
        return self

        #return self

class GetPeers(Queries):
    
    def __init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        query,sender,info,dist):
        Queries.__init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        query,sender)
        self.infohash= info
        self.dist_from_sender=dist

    def get_peers_query(self):
        
        return self


class FindNode(Queries):
    
    def __init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        query,sender,target):
        Queries.__init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        query,sender)
        self.target_id= target

    def find_node_query(self):
        
        return self

class Ping(Queries):
    
    def __init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        query,sender):
        Queries.__init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        query,sender)

    def ping_query(self):
        
        return self
class AnnouncePeer(Queries):
    
    def __init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        query,sender,info,port,token,dist):
        Queries.__init__(self,src,dst,hex,tid,ts,absts,ver,msg,
                        query,sender)
        self.infohash= info
        self.btport=port
        self.token=token
        self.distance = dist
        self.dist_from_sender=dist

    def announce_peer_query(self):
        
        return self


    
