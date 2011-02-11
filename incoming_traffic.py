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


import core.identifier as identifier
import core.pymdht as pymdht
import logging

import plugins.lookup_a16 as lookup_m_mod
import plugins.routing_nice_rtt as routing_m_mod

#logs_path = './interactive_logs/'
logs_path = '.'

logs_level = logging.DEBUG  # This generates HUGE (and useful) logs
#logs_level = logging.INFO  # This generates some (useful) logs
#logs_level = logging.WARNING  # This generates warning and error logs


if len(sys.argv) == 4:
    my_addr = ('127.0.0.1', int(sys.argv[1]))
    id_ = identifier.Id(sys.argv[2]).generate_close_id(int(sys.argv[3]))
    dht = pymdht.Pymdht(my_addr, logs_path, routing_m_mod, lookup_m_mod,
                        None, logs_level, id_)
    while (True):
        time.sleep(5)
else:
    print 'usage: python incoming_traffic.py dht_port info_hash log_distance'
