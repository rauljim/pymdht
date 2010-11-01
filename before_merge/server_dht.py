# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import time
import sys
import pdb
#import guppy

import logging, logging_conf
logs_path = '.'
logs_level = logging.DEBUG # This generates HUGE (and useful) logs
#logs_level = logging.INFO # This generates some (useful) logs
#logs_level = logging.WARNING # This generates warning and error logs
#logs_level = logging.CRITICAL

import identifier
import kadtracker


#hp = guppy.hpy()

def peers_found(peers):
    if peers:
        print time.asctime(), 'got peers'
    else:
        print 'END OF LOOKUP'


info_hashes = (
    identifier.Id('f4e978569bfe29fd064744964b3b9f2f1c0c4042'),
    identifier.Id('69b45eca422279ee5324f2f765e67e6e867fb4fd'),
    identifier.Id('1683b3e58b6e4ad54fb600046942f84cbc779158'),
    identifier.Id('8647c10a2c96c8d0c49365397068312ae15c3851'),
    identifier.Id('24ec1f97b8288b15943096278dcf11c4487416e0'),
    identifier.Id('fb2b0896db0b153b044f2933eb9f28fd7e5dd619'),
    identifier.Id('841091657dab9bfb14374f91cd7a060d529abd8f'),
    identifier.Id('54f38598195829548d4176fd35697ef93605c159'),
    identifier.Id('3d74c23bd491269476a95aafce7970b67636811d'),
    identifier.Id('8f0af6f25e90d257e0c20a9ec3a5a35ad5fb5ebe'),
    identifier.Id('bcbdb9c2e7b49c65c9057431b492cb7957c8a330'),
    identifier.Id('a036cf0a6ee286f3fa7ec032e4014242df627c1a'),
    identifier.Id('e2c71f9f6dd6b3cc8aa12dc2444b631091bbb7e6'),
    identifier.Id('675a2e8535d101bd986d2820a2059bb7e011fc19'),
    identifier.Id('0112b5ba9618dab49395eeb2bc77cc929b7d9259'),
    identifier.Id('daae95a363a6d13bbe786d488b475ae81c371565'),
    identifier.Id('371db693fab57084d70cd7cd43a716b6c66dd73f'),
    identifier.Id('d8191961111f04a687b59d68c658f6ddc43cc176'),
    identifier.Id('51bdaa8ae1bfa0df8d3e29de17407ea20c5109a4'),
    identifier.Id('b15f4584e41086b18d86c35eced2e72b90c56e8b'),
    identifier.Id('acf47be77a69cf8294053d1358c79b990b0e98ce'),
    identifier.Id('bee3adbda692e2d4daa282482972843e19891db4'),
    identifier.Id('3623f5d26ed9e42078855f8a7c4217ce8efde783'),
    identifier.Id('c700d7326777bb6d64a3f578f21ee2bcb8aa0b3a'),
    identifier.Id('145f5e0970951a64795d45bfc9e7e7a0b8224895'),
    identifier.Id('f1876fdf5978828760042864225d08f6d358e3a3'),
    identifier.Id('85d3261be46198bfaa4892e8122896e84bb1b499'),
    identifier.Id('fc4bb6afb4d51dd035ba91965349b0bb595858fe'),
    identifier.Id('1bd2c8c001d78b19ef3dc3105c86b84b859e03f9'),
    identifier.Id('4493085265179525d1d42b6d8b7dc4ad9500fc19'),
#    identifier.Id('a41210064615944c4b79aec5ada06d5d99077db9'),
    )
    
if len(sys.argv) == 4 and sys.argv[0] == 'server_dht.py':
    logging.critical('argv %r' % sys.argv)
    RUN_DHT = True
    my_addr = (sys.argv[1], int(sys.argv[2])) #('192.16.125.242', 7000)
    logs_path = sys.argv[3]
    print 'logs_path:', logs_path
    logging_conf.setup(logs_path, logs_level)
    dht = kadtracker.KadTracker(my_addr, logs_path)
else:
    RUN_DHT = False
    print 'usage: python server_dht.py dht_ip dht_port path'
    
lookup_times = {}
try:
    print 'Type Control-C to exit.'
    i = 0
    while (RUN_DHT):
        for info_hash in info_hashes:
            #splitted_heap_str = str(hp.heap()).split()
            #print i, splitted_heap_str[10]
            #dht.print_routing_table_stats()
            time.sleep(20 * 60)
            print time.asctime(), 'Getting peers...'
            lookup_times[info_hash] = time.time()
            dht.get_peers(info_hash, peers_found)
            #time.sleep(1.5)
            #dht.stop()
            #pdb.set_trace()
            i = i + 1
except (KeyboardInterrupt):
    dht.stop()
    

