# Copyright (C) 2009-2011 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import sys

import core.ptime as time
import core.identifier as identifier

MIN_BT_PORT = 1024
MAX_BT_PORT = 2**16


def _on_peers_found(start_ts, peers, src_node):
    if peers:
        print '[%.4f] %d peer(s)' % (time.time() - start_ts, len(peers))
        print peers
    else:
        print '[%.4f] END OF LOOKUP' % (time.time() - start_ts)

def command_user_interface(dht):
    print '\nType "exit" to stop the DHT and exit'
    print 'Type "help" if you need'
    while (1):
        input = sys.stdin.readline().strip().split()
        if not input:
            continue
        command = input[0]
        if command == 'help':
            print '''
Available commands are:
- help
- fast info_hash bt_port
- exit
- m                  Memory information
'''
        elif command == 'exit':
            dht.stop()
            break
        elif command == 'm':
            import guppy
            h = guppy.hpy()
            print h.heap()
        elif command == 'fast':
            if len(input) != 3:
                print 'usage: fast info_hash bt_port'
                continue
            try:
                info_hash = identifier.Id(input[1])
            except (identifier.IdError):
                print 'Invalid info_hash (%s)' % input[1]
                continue
            try:
                bt_port = int(input[2])
            except:
                print 'Invalid bt_port (%r)' % input[2]
                continue
            if 0 < bt_port < MIN_BT_PORT:
                print 'Mmmm, you are using reserved ports (<1024). Try again.'
                continue
            if bt_port > MAX_BT_PORT:
                print "I don't know about you, but I find difficult",
                print "to represent %d with only two bytes." % (bt_port),
                print "Try again."
                continue
            dht.get_peers(time.time(), info_hash,
                          _on_peers_found, bt_port)
        else:
            print 'Invalid input: type help'
