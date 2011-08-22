# Copyright (C) 2010 Sara Dar
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import filereader as fread
#import matchqandr as qrmatch
import decimal
import queryparser as qparser
import responseparser as rparser
import errorparser as eparser
import filters

#from profilestats import profile


import aliasing

class MainClass:
    def __init__(self):
        self.res=[]
        self.que=[]
        self.qr=[]
    def get_data_from_file(self,filename):
        
        fobj = fread.FileReader()
        dobj = fread.Data()
        packets_list = dobj.get_data(filename)
        return packets_list


#    @profile
    def open_file(self,filename):
       
        
        objQ=qparser.QueriesBisector()
        objR=rparser.ResponseBisector()
        objE=eparser.ErrorBisector()
        #objQR=qrmatch.MatchQandR()
        #self.infohashlist=objQ.find_infohash_from_file()
        packets_list = self.get_data_from_file(filename)
        self.res = objR.all_responses(packets_list)#list of all responses
        self.que = objQ.all_queries(packets_list)#list of all queries
        self.err = objE.all_errors(packets_list)
        #for i in self.err:
         #   print i.error
        self.qre = self.all_query_response_inline(self.que,self.res,self.err)
   
        

        return self.que,self.res,self.err,self.qre
    





    def all_query_response_inline(self, qlist_orig, rlist_orig,elist_orig):
        qlist = qlist_orig #qlist = [elem for elem in qlist_orig]
        rlist = rlist_orig #rlist = [elem for elem in rlist_orig]
        elist = elist_orig
        #raul: I think we don't need to have copies of these anymore
        rlist_size = len(rlist)
        result=[]
        elist_size=0
        if elist:
            elist_size = len(elist)
        #Qrecord = self.a.all_queries(rawpacketlist)
        #Rrecord = self.b.all_response(rawpacketlist)
        #for i,line in enumerate(rlist):
        #print len(rlist)
        response_index = 0 # Response previous to this index predate the
        # current query (and should not be considered)
  

        for qrecord in qlist:
            record_found = False
            for i in xrange(response_index, rlist_size):
                rrecord = rlist[i]
                timeout_ts = qrecord.ts + 60 # One minute timeout
                #TODO: explain this trade-off
                if rrecord.ts < qrecord.ts: # This reponse PREDATES the
                    # query (ignore it)
                    response_index = i + 1
                    continue
                if rrecord.ts > timeout_ts:
                    break # Response not found (probably never got it)
                    # If the response arrived after one minute it will
                    # show up as a "response without query"
                if (qrecord.dst_addr == rrecord.src_addr 
                    and qrecord.hexaTid == rrecord.hexaTid):
                    #NOTICE we do not check that a response has been
                    #already matched. If so, a response will be
                    #associated to TWO queries and the second response
                    #(if any) will show up as "response without query"
                    record_found = True
                    break
            if record_found:
                self.set_distances(qrecord, rrecord)
                RTT = self.find_rtt(qrecord.ts, rrecord.ts)
                result.append([qrecord, rrecord, RTT])
                #rlist.remove(rrecord)
            elif not elist_size==0:
                for erecord in elist:
                    if (qrecord.dst_addr == erecord.src_addr 
                    and qrecord.hexaTid == erecord.hexaTid):
                        RTT = self.find_rtt(qrecord.ts, erecord.ts)
                        result.append([qrecord,erecord,RTT])
            else:
                #bogus=['bogus','-','-','-','-','-','-','-','-']
                rtt=0
                result.append([qrecord,'bogus',0])
            

        #if result:
        #    result=sorted(result,key=operator.itemgetter(3))
        return result

  
    def find_rtt(self,qts,rts):
        decimal.getcontext().prec = 4
        d=decimal.Decimal(str(rts-qts))
        
        rtt= (d*1)
        return rtt



    def set_distances(self,qrecord,rrecord):
        distancelist=[]
           
        if qrecord.query_type== 'get_peers':
            #print qrecord[7]
            infohash = qrecord.infohash
            dist_from_sender = infohash.log_distance(rrecord.sender_id)
            rrecord.dist_from_sender = dist_from_sender
             #rrecord[10]=[]
            if rrecord.nodes_ids:
                for i in range(len(rrecord.nodes_ids)):
                    distancelist.append(rrecord.nodes_ids[i].log_distance(infohash))
           
                rrecord.nodes_distances=distancelist   
        elif qrecord.query_type== 'find_node':
            targetid = qrecord.target_id #no infohash in findnode query
            if rrecord.nodes_ids:
                for elem in rrecord.nodes_ids:
                    distancelist.append(elem.log_distance(targetid))
  
                rrecord.nodes_distances=distancelist   
        
        elif qrecord.query_type== 'announce_peer':
            #print qrecord[7]
            infohash = qrecord.infohash
            dist_from_sender = infohash.log_distance(rrecord.sender_id)
            rrecord.dist_from_sender = dist_from_sender
        elif qrecord.query_type == 'ping':
            pass
        else:
            assert 0 # This should never happen

    def get_peers_query_response(self,list):
        result=[]
        #pointer = 0
        #j=0
        #recordFound=False
        #Qrecord = self.a.get_peers(list)
        #Rrecord = self.b.get_peers_response(list)
        for i,line in enumerate(list):
            if line[0].query_type=='get_peers':
                result.append(line)

        #if result:
        #    result=sorted(result,key=operator.itemgetter(3))
        return result

    
    def find_node_query_response(self,list):
        result=[]
        #pointer = 0
        #j=0
        #recordFound=False
        #Qrecord = self.a.get_peers(list)
        #Rrecord = self.b.get_peers_response(list)
        for i,line in enumerate(list):
            if line[0].query_type=='find_node':
                result.append(line)

        #if result:
        #    result=sorted(result,key=operator.itemgetter(3))
        return result

    def ping_query_response(self,list):
        result=[]
        #pointer = 0
        #j=0
        #recordFound=False
        #Qrecord = self.a.get_peers(list)
        #Rrecord = self.b.get_peers_response(list)
        for i,line in enumerate(list):
            if line[0].query_type=='ping':
                result.append(line)

        #if result:
        #    result=sorted(result,key=operator.itemgetter(3))
        return result

    def announce_peer_query_response(self,list):
        result=[]
        #pointer = 0
        #j=0
        #recordFound=False
        #Qrecord = self.a.get_peers(list)
        #Rrecord = self.b.get_peers_response(list)
        for i,line in enumerate(list):
            if line[0].query_type=='announce_peer':
                result.append(line)

        #if result:
        #    result=sorted(result,key=operator.itemgetter(3))
        return result

    def query_with_no_response(self,list):

        result=[]
        for i,line in enumerate(list):
            if line[1]=='bogus':
                result.append(line)

        return result

    def response_with_no_query_old(self,list,reslist,errlist):
        alltids=[]
        resp=[]
        err=[]
        result=[]
        for i,line in enumerate(list):
            alltids.append(line[0].tid)
        for i in range(len(reslist)):
            if not reslist[i].tid in alltids:
                resp.append(reslist[i])
        for i in range(len(errlist)):
            print errlist[i]
            if not errlist[i].tid in alltids:
                err.append(errlist[i])
        for item in resp:
            result.append(['bogus',item,0])
        for value in err:
            result.append(['bogus',value,0])
        return result


    def response_with_no_query(self,quelist,reslist,errlist):

        pass
#multiple problems here
        
    
    def filter(self,list,filtertext):
        
        #filtertext=self.filtertxt.GetValue()
        #filtered=filtertext.split()
        #self.filtertxt.SetValue(str(filtered))
        fobj=filters.Filters()
        f= fobj.check_filter_validity(filtertext)
        if f==True:
            fexpression=filtertext.split()
            a=fobj.filter_data(list,fexpression)
            return a

    def check_aliasing(self,qrlist,id):
        result=[]
        obj=aliasing.Aliasing()
        if id==1:
            result=obj.id_aliasing(qrlist)
        elif id==2:
            result=obj.ip_aliasing(qrlist)
        elif id==3:
            result=obj.transaction_aliasing(qrlist)
  
        return result

"""

    def get_queries(self,packlist):

        pass
    
    def get_responses(self,packlist):

        pass

    def show_match_all_qr(self,rawpacketlist):
        objqr=qr.MatchQandR()
        a=objqr.all_query_response_inline(rawpacketlist)
        return a

    def match_get_peers_qr(self,list):
        objqr=qr.MatchQandR()
        a=objqr.get_peers_query_response_inline(list)
        return a

    def match_find_node_qr(self,list):
        objqr=qr.MatchQandR()
        a=objqr.find_node_query_response_inline(list)
        return a

    def match_announce_peer_qr(self,list):
        objqr=qr.MatchQandR()
        a=objqr.announce_peer_query_response_inline(list)
        return a

    def match_ping_qr(self,list):
        objqr=qr.MatchQandR()
        a=objqr.ping_query_response_inline(list)
        self.list=a
        self.loadList1()

    def query_with_no_response(self,list):
        objqnr=qr.MatchQandR()
        a=objqnr.query_with_no_response(list)
        self.list=a
        self.loadList1()

    def response_with_no_query(self,list):
        objrnq=qr.MatchQandR(self.filename)
        a=objrnq.response_with_no_query()
        return a


"""
#qr = MainClass().open_file('log2.pcap')

#print qr.destinations
#for i in range(len(qr)):
#    print qr[i][0].src_addr


