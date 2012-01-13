# Copyright (C) 2010 Sara Dar
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

# errors in data
import sys
import re
import operator
from socket import inet_ntoa
import string
#import pcap
#import dpkt
import binascii
import core.old_message as message
import filereader as fread

#import mainclass

class ErrorBisector:

    def __init__(self):
        pass


    def all_errors(self,packets_list):
        packetlist=packets_list
     
        allerrors = []
        err=''
        self.firstTs= packetlist.timestamps[0]
        for i, msg in enumerate(packetlist.messages):
            if msg.type == message.ERROR:
                tid = packetlist.transIDs[i]
                ts = packetlist.timestamps[i]
                src_addr = packetlist.sources[i]
                dst_addr = packetlist.destinations[i]
                err = self._parse_error(msg, tid, ts, src_addr, dst_addr)
            
                allerrors.append(err)
        return allerrors


    def _parse_error(self, msg, tid, ts, src_addr, dst_addr):

        hextid = binascii.hexlify(tid)
        relative_ts = round(ts - self.firstTs, 7) 
 
  
        err = Errors(src_addr, dst_addr, hextid,
                             tid, relative_ts, ts,
                             msg.version, msg.type,msg.error)
        error = err._get_data()
        return error



                                    
class Errors:

    def __init__(self,src,dst,hex,tid,ts,absts,ver,msg,error):

        self.src_addr=src
        self.dst_addr=dst
        self.hexaTid=hex
        self.tid=tid
        self.ts=ts
        self.absTs=absts
        self.version=ver
        self.msg_type=msg
        self.error = error

    def _get_data(self):
        return self


