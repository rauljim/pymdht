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
        self.values_rs = []
        self.peer_set = set()
        self.auth_responses = []
        self.closest_log_distances = []

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
                if not lookup.values_rs:
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
        num_lookups_without_peeers = 0
        auth_time_file = openf(self.label + '.l_time_auth', 'w')
        closest_time_file = openf(self.label + '.l_time_closest', 'w')
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
            auth_time = None
            closest_time = None
            for values_r in lookup.values_rs:
                num_peers_file.write('%d ' % len(values_r.peers))
                peers_time_file.write('%f ' % (values_r.time))
                if (not auth_time and
                    values_r.log_distance <= lookup.closest_log_distances[-1]):
                    auth_time = values_r.time
                if (not closest_time and
                    values_r.log_distance == lookup.closest_log_distances[0]):
                    closest_time = values_r.time
                
            if not lookup.values_rs: 
                num_lookups_without_peeers += 1
                continue
            time_file.write('%f\n' % (lookup.values_rs[0].time))
            num_peers_file.write('\n')
            peers_time_file.write('\n')
            swarm_size_file.write('%d\n' % (len(lookup.peer_set)))

            queries_file.write('%d\n' % (lookup.num_queries))
            queries_till_peers_file.write('%d\n' % (
                    lookup.num_queries_till_peers))

            auth_time_file.write('%.4f\n' % (auth_time))
            closest_time_file.write('%.4f\n' % (closest_time))

            c_ld_file.write('%d\n' % (lookup.closest_log_distances[0]))
                              
        
        print '%s: No peers for %d lookups' % (self.label,
                                              num_lookups_without_peeers)
