# Copyright (C) 2010 Sara Dar
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information               
import core.identifier as identifier

class Aliasing():
   def __init__(self):
        pass

   def ip_aliasing(self,qrlist):
      #ip alias mean multiple peers having same id
        mynewlist=[]
        mynewlist2=[]
        ipalias=[]
        hex_tid=[]
        address=[]
        record=[]
        record1=[]
        #self.query=que
        #self.response=res
        self.qrlist=qrlist
        #mynewlist.append('79.112.92.98')
        #mynewlist2.append(identifier.Id('ef0581e695c69df4090110fc3e9b9113924ad7c2'))

        for line in self.qrlist:
           if not line[0].src_addr[0] in mynewlist:
              mynewlist.append(line[0].src_addr[0])
              record.append(line)
              if not line[0].sender_id in mynewlist2:
                 mynewlist2.append(line[0].sender_id)
              elif line[0].sender_id in mynewlist2: 
                  #ipalias.append(line)
                  for item in record:
                     if item[0].sender_id == line[0].sender_id:
                        ipalias.append(item)

           if (not line[1]=='bogus') and (not line[1].src_addr[0] in mynewlist):
              mynewlist.append(line[1].src_addr[0])
              record1.append(line)
              if not line[1].sender_id in mynewlist2:
                 mynewlist2.append(line[1].sender_id)
              elif line[1].sender_id in mynewlist2: 
                  #ipalias.append(line)
                  for elem in record1:
                     if elem[1].sender_id == line[1].sender_id:
                        ipalias.append(elem)
                  
                  
        return ipalias  





   def id_aliasing(self,qrlist):
        mynewlist=[]
        mynewlist2=[]
        idalias=[]
        record=[]
        #self.query=que
        #self.response=res
        self.qrlist=qrlist
        #mynewlist2.append('24.8.65.85')
        #mynewlist.append(identifier.Id('ef0581e695c69df4090110fc3e9b9117929ad7c1'))

        for line in self.qrlist:
           if not line[0].sender_id in mynewlist:
              mynewlist.append(line[0].sender_id)
              record.append(line)
              if not line[0].src_addr[0] in mynewlist2:
                 mynewlist2.append(line[0].src_addr[0])
              elif line[0].src_addr[0] in mynewlist2: 
                  #ipalias.append(line)
                  for item in record:
                     if item[0].src_addr[0] == line[0].src_addr[0]:
                        idalias.append(item)

                    
        return idalias


   def transaction_aliasing(self,qrlist):

      self.qrlist=qrlist
      tids=[]
      transalias=[]
      for i,line in enumerate(self.qrlist):
         if not line[0].hexaTid in tids:
            tids.append(line[0].hexaTid)
         else:
            transalias.append(line[0].hexaTid)

      return transalias
         

      

"""

        for line in self.query:
           if not line.src_addr[0]in mynewlist:
               mynewlist.append(line.src_addr[0])
               if not line.sender_id in mynewlist2:
                  mynewlist2.append(line.sender_id)
               elif line.sender_id in mynewlist2:
                  a=mynewlist2.index(line.sender_id)
                  ipalias.append(line.sender_id)
                  address.append(mynewlist[a])
                  hex_tid.append(line.hexaTid)
                
        for line in self.response:
           if not line.src_addr[0]in mynewlist:
              mynewlist.append(line.src_addr[0])
              if not line.sender_id in mynewlist2:
                 mynewlist2.append(line.sender_id)
              elif line.sender_id in mynewlist2:
                 a=mynewlist2.index(line.sender_id)
                 ipalias.append(line.sender_id)
                 address.append(mynewlist[a])
                 hex_tid.append(line.hexaTid)
        print address
        print ipalias
        return ipalias,hex_tid,address





id_aliaisng
       for i,line in enumerate(self.query):
            if not line.sender_id in mynewlist:
                mynewlist.append(line.sender_id)
                if not line.src_addr[0] in mynewlist2:
                    mynewlist2.append(line.src_addr[0])
                else:
                    idalias.append(line.src_addr[0])
                
        for i,line in enumerate(self.response):
            if not line.sender_id in mynewlist:
                mynewlist.append(line.sender_id)
                if not line.src_addr[0] in mynewlist2:
                    mynewlist2.append(line.src_addr[0])
                else:
                    idalias.append(line.src_addr[0])






"""
