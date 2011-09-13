# Copyright (C) 2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

"""


"""

from parser_utils import openf
import core.message as message

import cdf

NUM_AUTH_REPLICAS = 3


class ValuesR(object):

    def __init__(self, time, log_distance, peers):
        self.time = time
        self.log_distance = log_distance
        self.peers = peers

        
class LookupInfo(object):

    def __init__(self, info_hash, start_ts):
        self.info_hash = info_hash
        self.start_ts = start_ts

        self.num_queries = 0
        self.num_queries_till_peers = 0
        self.values_rs = [] # responses with values
        self.peer_set = set()
        self.auth_responses = []
        self.closest_log_distances = []

class Parser(object):

    def __init__(self, label, my_addr):
        self.label = label
        self.my_addr = my_addr
        self.lookups = {} # LookupInfo dictionary

        self.num_lookups_without_peeers = 0

        self.auth_time_file = openf(self.label + '.l_time_auth', 'w')
        self.closest_time_file = openf(self.label + '.l_time_closest', 'w')
        self.c_ld_file = openf(self.label + '.l_c_ld', 'w')
        self.time_file = openf(self.label + '.l_time', 'w')
        self.queries_file = openf(self.label + '.l_queries', 'w')
        self.peers_time_file = openf(self.label + '.l_peers_time', 'w')
        self.num_peers_file = openf(self.label + '.l_num_peers', 'w')
        self.num_nodes_file = openf(self.label + '.l_num_nodes', 'w')
        self.swarm_size_file = openf(self.label + '.l_swarm_size', 'w')
        self.queries_till_peers_file = openf(
            self.label + '.l_queries_till_peers', 'w')

        
    def outgoing_msg(self, ts, dst_addr, msg):
        if msg.type == message.QUERY:
            if msg.query == message.GET_PEERS:
                # lookup query
                lookup = self.lookups.get(msg.info_hash, None)
                if not lookup:
                    for ih in self.lookups.keys():
                        l = self.lookups[ih]
                        if ts > l.start_ts + 200:
                            self._write_lookup(l)
                            del self.lookups[ih]
                    lookup = LookupInfo(msg.info_hash, ts)
                    self.lookups[msg.info_hash] = lookup
                    
                lookup.num_queries += 1
                if not lookup.values_rs:
                    lookup.num_queries_till_peers += 1

    def incoming_msg(self, ts, src_addr, msg, related_query):
        if not related_query:
            return
        peers = getattr(msg, 'peers', None)
        if not peers:
            return
        # This is a response WITH peers
        lookup = self.lookups.get(related_query.msg.info_hash, None)
        if lookup:
            log_distance =  lookup.info_hash.log_distance(msg.src_id)
            lookup.values_rs.append(
                ValuesR(ts - lookup.start_ts, log_distance, peers))
            for peer in peers:
                lookup.peer_set.add(peer)
            lookup.closest_log_distances.append(log_distance)
            lookup.closest_log_distances.sort()
            if len(lookup.closest_log_distances) > NUM_AUTH_REPLICAS:
                del lookup.closest_log_distances[NUM_AUTH_REPLICAS]

    def done(self):
        for lookup in self.lookups.itervalues():
            self._write_lookup(lookup)
        print '%s: No peers for %d lookups' % (self.label,
                                              self.num_lookups_without_peeers)

    def _write_lookup(self, lookup):
        auth_time = None
        closest_time = None
        for values_r in lookup.values_rs:
            self.num_peers_file.write('%d ' % len(values_r.peers))
            self.peers_time_file.write('%f ' % (values_r.time))
            if (not auth_time and
                values_r.log_distance <= lookup.closest_log_distances[-1]):
                auth_time = values_r.time
            if (not closest_time and
                values_r.log_distance == lookup.closest_log_distances[0]):
                closest_time = values_r.time
                
        if not lookup.values_rs: 
            self.num_lookups_without_peeers += 1
            return
        self.num_nodes_file.write('%d ' % len(lookup.values_rs))
        self.time_file.write('%f\n' % (lookup.values_rs[0].time))
        self.num_peers_file.write('\n')
        self.peers_time_file.write('\n')
        self.swarm_size_file.write('%d\n' % (len(lookup.peer_set)))
        
        self.queries_file.write('%d\n' % (lookup.num_queries))
        self.queries_till_peers_file.write('%d\n' % (
                lookup.num_queries_till_peers))
        
        self.auth_time_file.write('%.4f\n' % (auth_time))
        self.closest_time_file.write('%.4f\n' % (closest_time))
        
        self.c_ld_file.write('%d\n' % (lookup.closest_log_distances[0]))
        
        
        
