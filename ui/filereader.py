# Copyright (C) 2010 Sara Dar
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

#import sys
from socket import inet_ntoa
#import string
#import pcap
#import dpkt
#import binascii
#from StringIO import StringIO
import core.old_message as message
#import os
#import stat
#import pymdht.identifier as identifier
#import keyword
import cPickle


MY_ADDR = ("1.1.1.1", 1111)

class FileReader:
    fname=''
    def __init__(self):
        #self.dataobj=data()
        pass
    def file_reader(self,filename):
        msglist=[]
        srclist=[]
        tidlist=[]
        dstlist=[]
        tslist=[]
        option=None
        try:
            f=open(filename)
            pcap=dpkt.pcap.Reader(f)
            option=True
        except:
            pass
        if option==True:              
            for (ts, raw_packet) in pcap:
                try:
                    ip_packet=dpkt.ethernet.Ethernet(raw_packet).ip     
                    src_addr=(inet_ntoa(ip_packet.src), ip_packet.udp.sport)
           
                except (AttributeError):            
                    continue
    
                try:
                    msg = message.IncomingMsg(ip_packet.data.data,src_addr)
                    srclist.append(src_addr)
                    dstlist.append((inet_ntoa(ip_packet.dst), ip_packet.udp.dport))
                    tslist.append(ts)
                    msglist.append(msg)
                    tidlist.append(msg.tid)
       
                    #print msg.version
                except(message.MsgError):
                    #print 'ERROR:', ip_packet.data.data
                    continue
                #msglist.append(msg)
                #transid.append(ord(msg.tid[0]))
            assert len(dstlist) == len(srclist)
            assert len(dstlist) == len(tslist)
            assert len(dstlist) == len(msglist)
            assert len(dstlist) == len(tidlist)    
            f.close()
            return msglist,tidlist,tslist,srclist,dstlist
        else:
            try:
                for (ts, addr, is_outgoing, data) in cPickle.load(open(filename)):
                    if is_outgoing:
                        src_addr = MY_ADDR
                        dst_addr = addr
                    else:
                        src_addr = addr
                        dst_addr = MY_ADDR
                    try:
                        msg = message.IncomingMsg(data,src_addr)
                        srclist.append(src_addr)
                        dstlist.append(dst_addr)
                        tslist.append(ts)
                        msglist.append(msg)
                        tidlist.append(msg.tid)
           
                        #print msg.version
                    except(message.MsgError):
                        #print 'ERROR:', ip_packet.data.data
                        continue
                    #msglist.append(msg)
                    #transid.append(ord(msg.tid[0]))
                assert len(dstlist) == len(srclist)
                assert len(dstlist) == len(tslist)
                assert len(dstlist) == len(msglist)
                assert len(dstlist) == len(tidlist)
                return msglist,tidlist,tslist,srclist,dstlist
            except:
                pass

    
class Data:
    def __init__(self):
        messages=[]
        transIDs=[]
        timestamps=[]
        sources=[]
        destinations=[]

    def get_packet(self,packetlist):
        self.messages=packetlist.messages
        self.transIDs=packetlist.transIDs
        self.timestamps=packetlist.timestamps
        self.sources=packetlist.sources
        self.destinations=packetlist.destinations

        return self

    def get_data(self,filename):
        fobj=FileReader()
        mlist, tidls, tsls, srcls,dstls=fobj.file_reader(filename)
        self.messages=mlist
        self.transIDs=tidls
        self.timestamps=tsls
        self.sources=srcls
        self.destinations=dstls
         
        return self
