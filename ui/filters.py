# Copyright (C) 2010 Sara Dar
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information
import wx
import operator
import os
import binascii
import sys
#import matchqandr as qr
from socket import inet_ntoa
#import pcap
#import dpkt
import keyword
#import mappings as map
import decimal


class Filters:
    list=[]
    SrcAndDst=[]
    SrcAndDstAndTid=[]
    Tid=[]
    def __init__(self):
        #self.m=map.Mappings()
        pass

    def check_filter_validity(self,values):
        count=0
        j=3
        k=0
        parameters=['src','dst','data','tid','tid','srcport',
                    'dstport','token'
                    ,'qts','rts','RTT','infohash']
        operators=['==','!=','>=','<=','>','<',]
        keywords=['and','or']
        flist=values.split()
        #print filtered
        if len(flist)< 3:
            print'filter incomplete'
            return False
        elif len(flist)==3:
            count=1
        elif len(flist)>3:
             for j in range(len(flist)):
                 if keyword.iskeyword(flist[j]):
                     #print 'ok..it is key word',flist[j]
                     count = count + 1
        
                 j=j+4
        for i in range(count):
            if flist[k]in parameters:
                if not (flist[k]=='rts'or flist[k]=='qts' or flist[k]=='RTT'):
                    if (flist[k+1]== '==' or flist[k+1]== '!='):
                        pass
                    else:
                        print 'Wrong operator with wrong parameter'
                        return False
                k=k+1
            else:
                print 'wrong parameter',flist[k]
                #print 'i value is',k
                return False
            if flist[k]in operators:
                k=k+1
            else:
                print 'wrong operator',flist[k]
                return False
            if len(flist[k]) <= 50:
                k=k+1
            else:
                print 'wrong value',flist[k]
                return False
            if len(flist)> 3:
                if len(flist)>=k+4:
                    if flist[k]in keywords:
                        pass
                        k=k+1
                    else:
                        print 'wrong keyword',flist[k]
                        return False
                else:
                    print 'incomplete filter'
                    return False
        return True




    def filter_data(self,list1,fexlist):
        
        #length_filterlist = len(flist)
        count=0
        
        j=3
        k=3
        m=2
        n=0
        p=1
        #obj = qr.MatchQandR(filename)
        #list1=obj.all_query_response_inline()
        
      
        for j in range(len(fexlist)):
            if keyword.iskeyword(fexlist[j]):
                #print 'ok..it is key word',flist[j]
                count = count + 1
        
            j=j+4
        
            
        data1=self.get_data(fexlist[n],fexlist[p],fexlist[m],list1)
        if len(fexlist)< 4: 
            return data1
        elif len(fexlist)> 4:
            for i in range(count):
               
                n=n+4
                m=m+4
                p=p+4
                #if list[k]:
                if keyword.iskeyword(fexlist[k]):
                    if fexlist[k]== 'and':
                        k=k+4
                        if data1:
                            data1=self.get_data(fexlist[n],fexlist[p],
                                                fexlist[m],data1)
                    elif fexlist[k]== 'or':
                        k=k+4
                        data2 = self.get_data(fexlist[n],fexlist[p],
                                              fexlist[m],list1)
                        data1 = data1 + filter(lambda x: x not in data1,data2)
            return data1



    def get_data(self,parameter,operator, value,data):
        
          filterlist=[]
          if parameter == 'src'and operator == '==':
           
            #for i in range(len(list1)):
            filtered = filter(lambda x:x[0].src_addr[0]== value,data )
            #print data[0][0][0]
            return filtered

          elif parameter == 'src'and operator == '!=':
           
            #for i in range(len(list1)):
            filtered = filter(lambda x:not(x[0].src_addr[0]== value),data )
            #print data[0][0][0]
            return filtered

          elif parameter== 'dst' and operator == '==':
            #for i in range(len(list1)):

            filtered = filter(lambda x:not x[1]=='bogus' and 
                              x[1].src_addr[0] == value,data )
            #print data[1][0][0]
            return filtered

          elif parameter == 'dst'and operator == '!=':
            filtered = filter(lambda x:not x[1]=='bogus' and 
                              not(x[1].src_addr[0] == value),data )
            return filtered

          elif parameter == 'data'and operator == '==':
              filtered = filter(lambda x:x[0].query_type==value,data )
              return filtered

          elif parameter == 'data'and operator == '!=':
              filtered = filter(lambda x:not(x[0].query_type==value),data )
              return filtered
          
          elif parameter == 'tid' and operator == '==':
              filtered = filter(lambda x:x[0].hexaTid==value,data )
              return filtered

          elif parameter == 'tid' and operator == '!=':
              filtered = filter(lambda x:not(x[0].hexaTid==value),data )
              return filtered

          #elif parameter == 'tid' and operator == '==':
             # filtered = filter(lambda x:binascii.hexlify(x[0].tid)
            #                    ==binascii.hexlify(value),data )
           #   return filtered

          #elif parameter == 'tid' and operator == '!=':
          #    filtered = filter(lambda x:not(x[0].tid==value),data )
          #    return filtered
          elif parameter == 'srcport' and operator == '==':
              filtered = filter(lambda x:x[0].src_addr[1]
                                ==int(value),data )          
              return filtered

          elif parameter == 'srcport' and operator == '!=':
              filtered = filter(lambda x:not(x[0].src_addr[1]
                                             ==int(value)),data )
              return filtered

          elif parameter == 'dstport'and operator == '==':
              filtered = filter(lambda x:not x[1]=='bogus' 
                                and x[1].src_addr[1]==int(value),data )
              return filtered

          elif parameter == 'dstport' and operator == '!=':
              filtered = filter(lambda x:not x[1]=='bogus' and
                                not(x[1].src_addr[1]==int(value)),data )
              return filtered
          
          elif parameter == 'qts' or parameter == 'rts':
              if parameter == 'qts':
                  c=0
              elif parameter == 'rts':
                  c=1
              if operator == '==':
                  filtered = filter(lambda x:not x[c]=='bogus'
                                    and x[c].ts == float(value),data )
              elif operator == '!=':
                  filtered = filter(lambda x:not x[c]=='bogus'
                                    and not(x[c].ts == float(value)),data )
              elif operator == '<=':
                  filtered = filter(lambda x:not x[c]=='bogus'
                                    and x[c].ts <= float(value),data )
              elif operator == '>=':
                  filtered = filter(lambda x:not x[c]=='bogus'
                                    and x[c].ts >= float(value),data )
              elif operator == '<':
                  filtered = filter(lambda x:not x[c]=='bogus'
                                    and x[c].ts < float(value),data )
              elif operator == '>':
                  filtered = filter(lambda x:not x[c]=='bogus'
                                    and x[c].ts > float(value),data )
              return filtered

          elif parameter == 'RTT':
              decimal.getcontext().prec = 4
              val = decimal.Decimal(value)*1
              if operator == '==':
                  #print float(value)
                  #for item in data:
                  #    print item[2]
                  filtered = filter(lambda x:not x[1]=='bogus'
                                    and x[2]==val,data )
                  #print filtered
              elif operator == '!=':
                  filtered = filter(lambda x:not(x[2]==val),data)
              elif operator == '<=':
                  filtered = filter(lambda x:x[2]<=val,data )
              elif operator == '>=':
                  filtered = filter(lambda x:x[2]>=val,data )
              elif operator == '<':
                  filtered = filter(lambda x:x[2] < val,data )
              elif operator == '>':
                  filtered = filter(lambda x:x[2] > val,data )
              return filtered
          
          elif parameter == 'infohash':
              if operator == '==':
                    filtered = filter(lambda x:x[0].query_type == 'announce_peer' 
                                      or x[0].query_type == 'get_peers'
                                      and repr(x[0].infohash)==value,data )
              return filtered
          elif parameter == 'token':
              if operator == '==':
                  filtered1 = filter(lambda x:x[0].query_type == 'announce_peer'
                                         and x[0].token==value,data)
                  
                  filtered2 = filter (lambda x:not x[1]== 'bogus'
                                     and x[0].query_type == 'get_peers'
                                     and x[1].token ==value,data )
                  filtered = filtered1+filtered2
              return filtered
