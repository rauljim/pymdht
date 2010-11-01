# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import time
import sys

import logging, logging_conf
logs_path = 'interactive_logs'
logs_level = logging.DEBUG # This generates HUGE (and useful) logs
#logs_level = logging.INFO # This generates some (useful) logs
#logs_level = logging.WARNING # This generates warning and error logs

import identifier
import kadtracker


def peers_found(peers):
    if peers:
        print '[%.4f] %d peer(s)' % (time.time() - start_ts, len(peers))
    else:
        print '[%.4f] END OF LOOKUP' % (time.time() - start_ts)
        
def lookup_done():
    print 'Lookup DONE'
    print 'Type an info_hash (in hex digits): ',

def main():
    if len(sys.argv) == 4:
        my_addr = (sys.argv[1], int(sys.argv[2])) #('192.16.125.242', 7000)
        logs_path = sys.argv[3]
        logging_conf.setup(logs_path, logs_level)
        dht = kadtracker.KadTracker(my_addr, logs_path)
    else:
        print 'usage: python interactive_dht.py dht_ip dht_port log_path'
        return
    
    print 'Type "exit" to stop the DHT and exit'
    print 'Type an info_hash (in hex digits): ',
    while (1):
        input = sys.stdin.readline()[:-1]
        if input == 'exit':
            dht.stop()
            break
        try:
            info_hash = identifier.Id(input)
        except (identifier.IdError):
            print 'Invalid input (%s)' % input
            continue
        print 'Getting peers for info_hash %r' % info_hash
        global start_ts
        start_ts = time.time()
        dht.get_peers(info_hash, peers_found)
        
if __name__ == '__main__':
    main()


