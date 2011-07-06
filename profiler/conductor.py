#! /usr/bin/env python

# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information



import sys
sys.path.append('..')

import os
import pdb
import random
import datetime
import shutil

import logging
import core.ptime as time

import core.identifier as identifier
import core.pymdht as pymdht
import ut2mdht.ut2mdht as ut2pymdht

import plugins.routing_bep5 as r_bep5
import plugins.routing_nice as r_nice
import plugins.routing_nice_rtt as r_nice_rtt
import plugins.routing_nice_rtt64 as r_nice_rtt64
import plugins.routing_nice_rtt128 as r_nice_rtt128

import plugins.lookup_a4 as l_a4
import plugins.lookup_a8_m2 as l_a8_m2
import plugins.lookup_m3 as l_m3
import plugins.lookup_m3_a4 as l_m3_a4

#logs_level = logging.DEBUG # This generates HUGE (and useful) logs
#logs_level = logging.INFO # This generates some (useful) logs
#logs_level = logging.WARNING # This generates warning and error logs
logs_level = logging.CRITICAL


STARTUP_DELAY = 10 # delay between two DHT node startups
BOOTSTRAP_DELAY = 30  # delay between end of startup and lookups
LOOKUP_DELAY = 10 # delay between two lookups
ROUND_DELAY = 10 # delay between rounds
STOPPING_DELAY = 10

REMOVE_TORRENT_DELAY = 3

IP = '192.16.127.98'
PORT = 8000 

CONFIG = (
    #(ut2pymdht, (IP, PORT), '0', r_bep5, l_a4),
    (pymdht, (IP, PORT+1), '1', r_bep5, l_a4),
    #(pymdht, (IP, PORT+2), '2', r_nice, l_a4),
    #(pymdht, (IP, PORT+3), '3', r_nice_rtt, l_a4),
    #(pymdht, (IP, PORT+4), '4', r_nice_rtt64, l_a4),
    #(pymdht, (IP, PORT+5), '5', r_nice_rtt128, l_a4),
    #(pymdht, (IP, PORT+6), '6', r_bep5, l_a8_m2),
    #(pymdht, (IP, PORT+7), '7', r_nice, l_a8_m2),
    #(pymdht, (IP, PORT+8), '8', r_nice_rtt, l_a8_m2),
    #(pymdht, (IP, PORT+9), '9', r_nice_rtt64, l_a8_m2),
    #(pymdht, (IP, PORT+10), '10', r_nice_rtt128, l_a8_m2),
)

INFOHASHES = [line.strip() for line in open('infohashes.dat')]

def _on_peers_found((node_name, start_ts), peers):
    if peers:
        print '[%.4f] %s got %d peer(s)' % (time.time() - start_ts,
                                     node_name, len(peers))
    else:
        print '[%.4f] %s END OF LOOKUP' % (time.time() - start_ts, node_name)

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

    shutil.copy('infohashes.dat', results_path)
    shutil.copy('conductor.py', results_path)
    shutil.copy('parser.py', results_path)
    shutil.copy('plotter.py', results_path)
    shutil.copytree('parsers', os.path.join(results_path, 'parsers'))
    shutil.copytree('plotters', os.path.join(results_path, 'plotters'))


    captures_path = os.path.abspath(os.path.join(results_path, timestamp_str + '.pcap'))
    print 'Now, you need to start capturing netwok traffic'
    print 'Windows:\nWinDump.exe -C 500 -s 0 -w %s udp' % (captures_path)
    print 'Linux:\nsudo tcpdump -C 500 -s 0 -w %s udp' % (captures_path)
    print '-' * 70
    print 'Press ENTER to continue'
    sys.stdin.readline()

    
    nodes = []
    for mod, addr, node_name, r_mod, l_mod in _randompopper(CONFIG):
        # Create infohash generator
        infohash_gen = _randompopper(INFOHASHES)

        print 'Starting %s %r, %r %r...' % (node_name, addr,
                                            r_mod.__file__, l_mod.__file__),
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
            print  '%d  %s getting peers for info_hash %r' % (
                round_number, node_name, infohash)
            node.get_peers((node_name, time.time()),
                           infohash, _on_peers_found, 0)
            time.sleep(REMOVE_TORRENT_DELAY)
            try:
                remove_torrent_f = node.remove_torrent
            except:
                pass
            else:
                remove_torrent_f(infohash)
            time.sleep(LOOKUP_DELAY - REMOVE_TORRENT_DELAY)
        time.sleep(ROUND_DELAY)
        
    for node_name, node, _ in nodes:
        node.stop()
        print 'Stopping %s ...' % node_name,
        sys.stdout.flush()
        time.sleep(STOPPING_DELAY)
        print 'DONE'
    print '-' * 70
    print 'Now, stop the network capturing with Ctr-C'
    
if __name__ == '__main__':
    main()


