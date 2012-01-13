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
#import ut2mdht.ut2mdht as ut2mdht

import plugins.routing_bep5 as r_bep5
import plugins.routing_nice as r_nice
import plugins.routing_nice_rtt as r_nice_rtt
import plugins.routing_nice_rtt64 as r_nice_rtt64

import plugins.lookup_a4 as l_a4
import plugins.lookup_a16 as l_a16
import plugins.lookup_m3 as l_m3
import plugins.lookup_m3_a4 as l_m3_a4

#logs_level = logging.DEBUG # This generates HUGE (and useful) logs
#logs_level = logging.INFO # This generates some (useful) logs
#logs_level = logging.WARNING # This generates warning and error logs
logs_level = logging.CRITICAL


STARTUP_DELAY = 20 # delay between two DHT node startups
BOOTSTRAP_DELAY = 60  # delay between end of startup and lookups
LOOKUP_DELAY = 10 # delay between two lookups
ROUND_DELAY = 20 # delay between rounds
STOPPING_DELAY = 1

REMOVE_TORRENT_DELAY = 5



CONFIG = (
    [pymdht, ('192.16.127.98', 7010), 'ns0', r_nice, l_a4],
    [pymdht, ('192.16.127.98', 7011), 'ns1', r_nice, l_a4],
    [pymdht, ('192.16.127.98', 7012), 'ns2', r_nice, l_a4],
    [pymdht, ('192.16.127.98', 7013), 'ns3', r_nice, l_a4],
    [pymdht, ('192.16.127.98', 7014), 'ns4', r_nice, l_a4],
    [pymdht, ('192.16.127.98', 7015), 'ns5', r_nice, l_a4],
    [pymdht, ('192.16.127.98', 7016), 'ns6', r_nice, l_a4],
    [pymdht, ('192.16.127.98', 7017), 'ns7', r_nice, l_a4],
    [pymdht, ('192.16.127.98', 7018), 'ns8', r_nice, l_a4],
    [pymdht, ('192.16.127.98', 7019), 'ns9', r_nice, l_a4],
)

# Add a column with the node_id (close to info_hash)
for i, line in enumerate(open('infohashes.dat')):
    infohash = identifier.Id(line.strip())
    node_id = infohash.generate_close_id(131)
    CONFIG[i].append(node_id)
    

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

    shutil.copy('infohashes.dat', results_path)
    shutil.copy('conductor.py', results_path)
    shutil.copy('conductor_spy.py', results_path)
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
    sys.stdout.flush()
    #sys.stdin.readline()
    time.sleep(60)
    
    nodes = []
    for mod, addr, node_name, r_mod, l_mod, node_id in _randompopper(CONFIG):
        # Create infohash generator
        
        print 'Starting %s %r, %r %r %r...' % (node_name, addr,
                                               r_mod.__file__,
                                               l_mod.__file__,
                                               node_id),
        sys.stdout.flush ()
        node_path = os.path.join(results_path, node_name)
        os.mkdir(node_path)
        node = mod.Pymdht(addr, node_path, r_mod, l_mod, None,
                          logs_level, node_id)
        nodes.append((node_name, node))
        print 'DONE'
        time.sleep(STARTUP_DELAY)

    #Leave them some time to bootstrap
    time.sleep(BOOTSTRAP_DELAY)

    running = True
    try:
        while 1:
            time.sleep(10000)
    except KeyboardInterrupt:
        pass

    for node_name, node in nodes:
        node.stop()
        print 'Stopping %s ...' % node_name,
        sys.stdout.flush()
        time.sleep(STOPPING_DELAY)
        print 'DONE'
    print '-' * 70
    print 'Now, stop the network capturing with Ctr-C'
    
if __name__ == '__main__':
    main()


