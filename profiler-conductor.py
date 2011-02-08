#! /usr/bin/env python

# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information



import sys
import os
import pdb
import random
import datetime
import shutil

import logging
import core.ptime as time

import core.identifier as identifier
import core.pymdht as pymdht
#import ut2mdht.ut2mdht as ut2mdht

import plugins.routing_nice_rtt as r_nice_rtt

import plugins.lookup_a16 as l_a16

logs_level = logging.DEBUG # This generates HUGE (and useful) logs
#logs_level = logging.INFO # This generates some (useful) logs
#logs_level = logging.WARNING # This generates warning and error logs
#logs_level = logging.CRITICAL


STARTUP_DELAY = 20 # delay between two DHT node startups
BOOTSTRAP_DELAY = 60  # delay between end of startup and lookups
LOOKUP_DELAY = 10 # delay between two lookups
ROUND_DELAY = 20 # delay between rounds
STOPPING_DELAY = 1

REMOVE_TORRENT_DELAY = 5


print '********************* CHECK DHT node config ********************'

CONFIG = (
    (pymdht, ('192.16.125.245', 7008), 'ns8', r_nice_rtt, l_a16),
)

INFOHASHES = [line.strip() for line in open('infohashes.dat')]

def _on_peers_found(lookup_id, peers):
    if peers:
        print '[%.4f] %d peer(s)' % (time.time(), len(peers))
    else:
        print '[%.4f] END OF LOOKUP' % (time.time())

def _randompopper(seq):
    """
    Make a copy of the sequence and return a generator. This generator will
    yield a random element popped from the sequence until all the elements
    have been popped.
    """
    random_seq = [e for e in seq]
    while random_seq:
        index = random.randint(0, len(random_seq) - 1)
        yield random_seq.pop(index)
        

def main():

    now = datetime.datetime.now()
    timestamp_str = now.strftime("%Y%m%d-%H%M%S")

    results_path = timestamp_str + '_tag'
    os.mkdir(results_path)

    shutil.copy('profiler-conductor.py', results_path)
    shutil.copy('infohashes.dat', results_path)
    
    
    nodes = []
    for mod, addr, node_name, r_mod, l_mod in _randompopper(CONFIG):
        # Create infohash generator
        infohash_gen = _randompopper(INFOHASHES)

        print 'Starting', node_name, '...',
        sys.stdout.flush ()
        node_path = os.path.join(results_path, node_name)
        os.mkdir(node_path)
        node = mod.Pymdht(addr, node_path, r_mod, l_mod, None, logs_level)
        nodes.append((node_name, node, infohash_gen))
        print 'DONE'
        time.sleep(STARTUP_DELAY)

    #Leave them some time to bootstrap
    time.sleep(BOOTSTRAP_DELAY)

    running = True
    for round_number in xrange(len(INFOHASHES)):
        # In every round, DHT nodes are randomly ordered
        for node_name, node, infohash_gen in _randompopper(nodes):
            # Every DHT node performs a lookup
            infohash = identifier.Id(infohash_gen.next())
            print  '%d [%.4f] %s getting peers for info_hash %r' % (
                round_number, time.time(), node_name, infohash)
            node.get_peers(None, infohash, _on_peers_found, 0)
            time.sleep(REMOVE_TORRENT_DELAY)
            node.remove_torrent(infohash)
            time.sleep(LOOKUP_DELAY - REMOVE_TORRENT_DELAY)
        time.sleep(ROUND_DELAY)
        
    for node_name, node, _ in nodes:
        node.stop()
        print 'Stopping %s ...' % node_name,
        sys.stdout.flush()
        time.sleep(STOPPING_DELAY)
        print 'DONE'
    
if __name__ == '__main__':
    main()


