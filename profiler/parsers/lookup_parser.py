# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""


"""

from parser_utils import openf
import core.message as message

import cdf

class LookupInfo(object):

    def __init__(self, info_hash, start_ts):
        self.info_hash = info_hash
        self.start_ts = start_ts

        self.num_queries = 0
        self.num_queries_till_peers = 0
        self.ts_peers = []
        self.peer_set = set()
        self.closest_log_distance = 160
        self.ctime = 0

class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr

        self.tids = {} # Key is tid[0] and value is the (addr, lookup)
                       # associated
        self.lookups = {}

    def outgoing_msg(self, ts, dst_addr, msg):
        if msg.type == message.QUERY:
            if msg.query == message.GET_PEERS:
                # lookup query
                lookup = self.lookups.get(msg.info_hash, None)
                if not lookup:
                    lookup = LookupInfo(msg.info_hash, ts)
                    self.lookups[msg.info_hash] = lookup
                self.tids[msg.tid[0]] = (dst_addr, lookup)
                lookup.num_queries += 1
                if not lookup.ts_peers:
                    lookup.num_queries_till_peers += 1

    def incoming_msg(self, ts, src_addr, msg):
        if msg.type != message.RESPONSE:
            return
        peers = getattr(msg, 'peers', None)
        if not peers:
            return
        # This is a response WITH peers
        try:
            addr, lookup = self.tids[msg.tid[0]]
        except (KeyError):
            print 'response with peers to unknown query'
            return
        del self.tids[msg.tid[0]]
        if addr == src_addr:
            lookup.ts_peers.append((ts, peers))
            for peer in peers:
                lookup.peer_set.add(peer)
            log_distance =  lookup.info_hash.log_distance(msg.src_id)
            if log_distance < lookup.closest_log_distance:
                lookup.closest_log_distance = log_distance
                lookup.ctime = ts - lookup.start_ts
        


    def done(self):
        num_lookups_without_peeers = 0
        ctime_file = openf(self.label + '.l_ctime', 'w')
        c_ld_file = openf(self.label + '.l_c_ld', 'w')
        time_file = openf(self.label + '.l_time', 'w')
        queries_file = openf(self.label + '.l_queries', 'w')
        peers_time_file = openf(self.label + '.l_peers_time', 'w')
        num_peers_file = openf(self.label + '.l_num_peers', 'w')
        swarm_size_file = openf(self.label + '.l_swarm_size', 'w')
        queries_till_peers_file = openf(
            self.label + '.l_queries_till_peers', 'w')
        lookup_times = []
        lookup_queries = []
        for lookup in self.lookups.values():
            for ts, peers in lookup.ts_peers:
                num_peers_file.write('%d ' % len(peers))
                peers_time_file.write('%f ' % (ts - lookup.start_ts))
            if lookup.ts_peers:
                lookup_time = lookup.ts_peers[0][0] - lookup.start_ts
                lookup_times.append(lookup_time)
                time_file.write('%f\n' % (lookup_time)) 
                num_peers_file.write('\n')
                peers_time_file.write('\n')
                swarm_size_file.write('%d\n' % (len(lookup.peer_set)))
            else:
                num_lookups_without_peeers += 1
                
            lookup_queries.append(lookup.num_queries)
            queries_file.write('%d\n' % (lookup.num_queries))
            queries_till_peers_file.write('%d\n' % (
                    lookup.num_queries_till_peers))
            ctime_file.write('%.4f\n' % (lookup.ctime))
            c_ld_file.write('%d\n' % (lookup.closest_log_distance))
                              
        time_cdf_file = openf(self.label + '.l_time.cdf', 'w')
        queries_cdf_file = openf(self.label + '.l_queries.cdf', 'w')
        for cum, value in cdf.cdf(lookup_times):
            time_cdf_file.write('%.4f\t%.4f\n' % (cum, value))
        for cum, value in cdf.cdf(lookup_queries):
            queries_cdf_file.write('%.4f\t%d\n' % (cum, value))

        
        print '%s: No peers for %d lookups' % (self.label,
                                              num_lookups_without_peeers)
