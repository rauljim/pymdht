'''
This script logs information about the incoming messsages to a node in the DHT.
It positions a node in the DHT to a given log distance from a given info hash.
It prints a log in the standart output. There are four types of messages
it logs:

1)

timestamp "PI"

timestamp: local time of the announcement
"PI": ping query


2)

timestamp "FN"

timestamp: local time of the announcement
"FN": find node query


3)

timestamp "GP" "IH:" <Id: info_hash> "querier:" (ip,port)

timestamp: local time of the announcement
info_hash: info hash of the get peers query
(ip, port): IP address and UDP port of the querier


4)

timestamp "GP" "IH:" <Id: info_hash> "announcer:" (ip,port)

timestamp: local time of the announcement
info_hash: info hash of the announcement
(ip, port): IP address and UDP port of the announcer



As the log information is printed in the standard output, it's recommended
to redirect the output to a file.'''


import time
import sys
import string

sys.path.append('./lib_kadtracker/')

import identifier
import kadtracker
import logging
import logging_conf


logs_path = './lib_kadtracker/interactive_logs/'

#logs_level = logging.DEBUG  # This generates HUGE (and useful) logs
#logs_level = logging.INFO  # This generates some (useful) logs
logs_level = logging.WARNING  # This generates warning and error logs


if len(sys.argv) == 4:
    logging_conf.setup(logs_path, logs_level)
    my_addr = ('127.0.0.1', int(sys.argv[1]))
    logs_path = './lib_kadtracker/interactive_logs/'
    id_ = identifier.Id(sys.argv[2]).generate_close_id(int(sys.argv[3]))
    dht = kadtracker.KadTracker(my_addr, logs_path, id_)
    while (True):
        time.sleep(5)
else:
    print 'usage: python incoming_traffic.py dht_port info_hash log_distance'
