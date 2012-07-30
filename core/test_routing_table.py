# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import ptime as time
import logging, logging_conf

from unittest import TestCase, main

import test_const as tc

import node

from routing_table import *

logging_conf.testing_setup(__name__)
logger = logging.getLogger('dht')

MAX_RNODES = 2
NODES_PER_BUCKET = 4

class TestBucket(TestCase):


    def test_(self):
        self.b = Bucket(NODES_PER_BUCKET, set())
        # The bucket is empty
        self.assertEqual(len(self.b) , 0)
        self.assertTrue(not self.b)
        # There is plenty of room
        for i in range (NODES_PER_BUCKET+1):
            self.assertTrue(self.b.there_is_room(i))

        # A rnode is added
        self.b.add(tc.CLIENT_NODE.get_rnode(1))
        # The bucket has a rnode now
        self.assertEqual(len(self.b) , 1)
        self.assertTrue(self.b)
        self.assertTrue(self.b.there_is_room(NODES_PER_BUCKET - 1))
        self.assertTrue(not self.b.there_is_room(NODES_PER_BUCKET))

        # The rnode is removed
        self.b.remove(tc.CLIENT_NODE)
        # The bucket is empty again
        self.assertEqual(len(self.b), 0)
        self.assertTrue(self.b.there_is_room(NODES_PER_BUCKET))
        
        # It is wrong to remove the rnode again
        self.assertRaises(Exception, self.b.remove, tc.CLIENT_NODE)
        # Or any not existing node, for that matter
        self.assertRaises(Exception, self.b.remove, tc.SERVER_NODE)

        # get_stalest_rnode return None when the bucket is empty
        self.assertEqual(self.b.get_stalest_rnode(), None)

        # Let's fill the bucket in
        for i in range(NODES_PER_BUCKET):
            self.b.add(tc.NODES[i].get_rnode(1))

        self.assertTrue(not self.b.there_is_room())
        self.assertEqual(self.b.get_stalest_rnode(), tc.NODES[0])

        # Remove stalest node
        self.b.remove(tc.NODES[0])
        self.assertTrue(self.b.there_is_room())
        self.assertEqual(self.b.get_stalest_rnode(), tc.NODES[1])

        # RNODES[1] gets refreshed
        rnode = self.b.get_rnode(tc.NODES[1])
        #########################rnode.on_response_received()
        rnode.last_seen = time.time()
        ##############
        self.assertEqual(self.b.get_stalest_rnode(), tc.NODES[2])

        # Complete coverage
        '%r' % self.b


    
    def test(self):
        b1 = Bucket(2, set())
        self.assertTrue(b1.get_rnode(tc.CLIENT_NODE) is None)
        self.assertEqual(len(b1), 0)
        self.assertFalse(b1)
        self.assertTrue(b1.there_is_room())
        self.assertTrue(b1.there_is_room(2))
        self.assertFalse(b1.there_is_room(3))
        self.assertTrue(b1.get_freshest_rnode() is None)
        self.assertTrue(b1.get_stalest_rnode() is None)

        rnode = tc.CLIENT_NODE.get_rnode(1)
        rnode.rtt = .2
        b1.add(rnode)
        self.assertEqual(b1.get_rnode(tc.CLIENT_NODE), tc.CLIENT_NODE)
        self.assertEqual(len(b1), 1)
        self.assertTrue(b1)
        self.assertTrue(b1.there_is_room())
        self.assertFalse(b1.there_is_room(2))
        self.assertFalse(b1.there_is_room(3))
        self.assertEqual(b1.get_freshest_rnode(), tc.CLIENT_NODE)
        self.assertEqual(b1.get_stalest_rnode(), tc.CLIENT_NODE)
        self.assertEqual(b1.sorted_by_rtt(), [tc.CLIENT_NODE])

        rnode = tc.SERVER_NODE.get_rnode(1)
        rnode.rtt = .1
        b1.add(rnode)
        self.assertEqual(b1.get_rnode(tc.CLIENT_NODE), tc.CLIENT_NODE)
        self.assertEqual(len(b1), 2)
        self.assertTrue(b1)
        self.assertFalse(b1.there_is_room())
        self.assertFalse(b1.there_is_room(2))
        self.assertFalse(b1.there_is_room(3))
        self.assertEqual(b1.get_freshest_rnode(), tc.SERVER_NODE)
        self.assertEqual(b1.get_stalest_rnode(), tc.CLIENT_NODE)
        self.assertEqual(b1.sorted_by_rtt(), [tc.SERVER_NODE, tc.CLIENT_NODE])
        
        self.assertRaises(AssertionError, b1.add, tc.CLIENT_NODE.get_rnode(1))
        b1.remove(tc.CLIENT_NODE)
        self.assertEqual(b1.get_rnode(tc.CLIENT_NODE), None)
        self.assertEqual(len(b1), 1)
        self.assertTrue(b1)
        self.assertTrue(b1.there_is_room())
        self.assertFalse(b1.there_is_room(2))
        self.assertFalse(b1.there_is_room(3))
        self.assertEqual(b1.get_freshest_rnode(), tc.SERVER_NODE)
        self.assertEqual(b1.get_stalest_rnode(), tc.SERVER_NODE)
        self.assertEqual(b1.sorted_by_rtt(), [tc.SERVER_NODE])

        b2 = Bucket(2, set())
        self.assertNotEqual(b1,b2)
        self.assertTrue(b1 != b2)

        b3 = Bucket(2, set())
        b3.add(tc.CLIENT_NODE)
        self.assertNotEqual(b1, b3)
        self.assertTrue(b1 != b3)
        
        b4 = Bucket(2, set())
        b4.add(tc.SERVER_NODE)
        self.assertEqual(b1, b4)
        self.assertFalse(b1 != b4)
        
        b5 = Bucket(3, set())
        b3.add(tc.SERVER_NODE)
        self.assertNotEqual(b1, b5)
        self.assertTrue(b1 != b5)

        

class TestRoutingTable(TestCase):

    def setUp(self):
        nodes_per_bucket = [MAX_RNODES] * 160
        self.my_node = tc.CLIENT_NODE
        self.rt = RoutingTable(self.my_node,
                               nodes_per_bucket)

    def test_basics(self):
        empty_b = Bucket(MAX_RNODES, set())

        # Get empty superbucket
        log_distance = self.my_node.distance(tc.SERVER_NODE).log
        sbucket = self.rt.get_sbucket(log_distance)
        m_bucket = sbucket.main
        r_bucket = sbucket.replacement
        self.assertEqual(m_bucket, empty_b)
        self.assertEqual(r_bucket, empty_b)
        self.assertTrue(r_bucket.there_is_room())
        self.assertEqual(m_bucket.get_rnode(tc.SERVER_NODE), None)
        self.assertTrue(m_bucket.there_is_room(MAX_RNODES))
        self.assertTrue(not m_bucket.there_is_room(MAX_RNODES + 1))
        self.assertEqual(self.rt.num_rnodes, 0) # empty
        self.assertEqual(self.rt.get_main_rnodes(), [])

        # Add server_node to main bucket
        m_bucket.add(tc.SERVER_NODE)
        self.rt.num_rnodes += 1
        self.assertTrue(m_bucket.there_is_room())
        self.assertTrue(not m_bucket.there_is_room(MAX_RNODES))
        self.assertEqual(m_bucket.rnodes, [tc.SERVER_NODE])
        self.assertEqual(m_bucket.get_rnode(tc.SERVER_NODE), tc.SERVER_NODE)

        # Check updated table
        self.assertEqual(self.rt.num_rnodes, 1)
        self.assertEqual(self.rt.get_main_rnodes(), [tc.SERVER_NODE])
        sbucket = self.rt.get_sbucket(log_distance)
        m_bucket = sbucket.main
        r_bucket = sbucket.replacement
        
        # Let's add a node to the same bucket
        new_node = node.Node(tc.SERVER_NODE.addr,
                             tc.SERVER_NODE.id.generate_close_id(1))
        m_bucket.add(new_node)
        self.rt.num_rnodes += 1
        # full bucket
        self.assertTrue(not m_bucket.there_is_room())
        self.assertEqual(m_bucket.rnodes, [tc.SERVER_NODE, new_node])
        self.assertEqual(m_bucket.get_rnode(new_node), new_node)
        # Trying to add to the bucket will raise exception
        self.assertRaises(AssertionError, sbucket.main.add, tc.NODES[0])
        self.assertEqual(self.rt.num_rnodes, 2)
        self.assertEqual(self.rt.get_main_rnodes(),
            [tc.SERVER_NODE, new_node])

        ld_to_server = tc.SERVER_ID.distance(tc.CLIENT_ID).log
        self.assertEqual(self.rt.get_closest_rnodes(ld_to_server, 1, True),
            [tc.SERVER_NODE])
        self.assertEqual(self.rt.get_closest_rnodes(ld_to_server, 8, False),
            [tc.SERVER_NODE, new_node, tc.CLIENT_NODE])
        self.assertEqual(self.rt.get_closest_rnodes(ld_to_server, 8, False),
            [tc.SERVER_NODE, new_node, tc.CLIENT_NODE])
        self.assertEqual(self.rt.get_closest_rnodes(ld_to_server, 8, True),
            [tc.SERVER_NODE, new_node])

        sbucket = self.rt.get_sbucket(log_distance)
        m_bucket = sbucket.main
        
        m_bucket.remove(new_node)
        print self.rt.get_main_rnodes()
        self.rt.num_rnodes -= 1
        # there is one slot in the bucket
        self.assertTrue(m_bucket.there_is_room())
        self.assertTrue(m_bucket.get_rnode(new_node) is None)
        self.assertEqual(m_bucket.rnodes, [tc.SERVER_NODE])
        self.assertEqual(m_bucket.get_rnode(tc.SERVER_NODE), tc.SERVER_NODE)

        self.assertEqual(self.rt.num_rnodes, 1)
        self.assertEqual(self.rt.get_main_rnodes(), [tc.SERVER_NODE])
                     
        self.assertEqual(self.rt.get_closest_rnodes(ld_to_server, 8, True),
            [tc.SERVER_NODE])
    '''
    def _test_pop_sbucket_parameters(self):
        # no parameters raises AssertionError
        self.assertRaises(AssertionError, self.rt.pop_sbucket)
        # passing both parameters raises AssertionError
        self.assertRaises(AssertionError,
                      self.rt.pop_sbucket, tc.SERVER_NODE, 0)
        # the following pops are equivalent
        sbucket1 = self.rt.pop_sbucket(tc.SERVER_NODE)
        self.rt.put_sbucket(sbucket1)
        sbucket2 = self.rt.pop_sbucket(node_=tc.SERVER_NODE)
        self.rt.put_sbucket(sbucket2)
        sbucket3 = self.rt.pop_sbucket(
            log_distance=tc.CLIENT_NODE.log_distance(tc.SERVER_NODE))
        self.rt.put_sbucket(sbucket3)
        # check they are the same sbucket
        self.assertEqual(sbucket1.index, sbucket2.index, sbucket3.index)
        assert sbucket2 is sbucket1
        assert sbucket3 is sbucket1

    def _test_invalid_put(self):
        sbucket = SuperBucket(2, 2)
        # putting a sbucket which has not been popped raises PutError
        self.assertRaises(PutError, self.rt.put_sbucket, sbucket)

        sbucket3 = self.rt.pop_sbucket(log_distance=3)
        # putting a different sbucket whose index is not equal to the
        # one popped raises PutError
        self.assertRaises(PutError, self.rt.put_sbucket, sbucket)
        self.rt.put_sbucket(sbucket3)

        sbucket2 = self.rt.pop_sbucket(log_distance=2)
        # putting a different sbucket whose index is equal to the one
        # popped is OK
        assert sbucket != sbucket2
        self.rt.put_sbucket(sbucket)
    '''
    def test_get_closest_rnodes(self):
        log_distances = [2, 3, 5, 5, 6, 7, 7, 19]
        nodes = [node.Node(n.addr, tc.CLIENT_ID.generate_close_id(ld))
                           for n, ld in zip(tc.NODES, log_distances)]
        for node_ in nodes:
            log_distance = self.my_node.distance(node_).log
            sbucket = self.rt.get_sbucket(log_distance)
            sbucket.main.add(node_.get_rnode(log_distance))
            self.rt.num_rnodes += 1

        self.assertEqual(self.rt.get_closest_rnodes(0, 8, True),
            nodes)
        
        self.assertEqual(self.rt.get_closest_rnodes(0, 8, False),
            [tc.CLIENT_NODE] + nodes[:7])

        self.assertEqual(self.rt.get_closest_rnodes(0,
                                       max_rnodes=4,
                                       exclude_myself=True),
            nodes[:4])
        self.assertEqual(self.rt.get_closest_rnodes(0,
                                       max_rnodes=4,
                                       exclude_myself=False),
            [tc.CLIENT_NODE] + nodes[:3])

        self.assertEqual(self.rt.get_closest_rnodes(0,
                                       max_rnodes=20,
                                       exclude_myself=True),
            nodes)
        self.assertEqual(self.rt.get_closest_rnodes(0,
                                       max_rnodes=20,
                                       exclude_myself=False),
            [tc.CLIENT_NODE] + nodes)

        ld_to_7 = tc.CLIENT_NODE.distance(nodes[7]).log
        closest_nodes = self.rt.get_closest_rnodes(ld_to_7, 8,
                                                   exclude_myself=True)
        self.assertEqual(closest_nodes[0], nodes[7])
        self.assertTrue(closest_nodes[1] in nodes[5:7])
        self.assertTrue(closest_nodes[2] in nodes[5:7])
        self.assertEqual(closest_nodes[3], nodes[4])
        self.assertTrue(closest_nodes[4] in nodes[2:4])
        self.assertTrue(closest_nodes[5] in nodes[2:4])
        self.assertEqual(closest_nodes[6], nodes[1])
        self.assertEqual(closest_nodes[7], nodes[0])

        # complete coverage
        self.rt.print_stats()

    def test_get_sbucket_error(self):
        self.assertRaises(IndexError, self.rt.get_sbucket, -2)
        self.assertRaises(IndexError, self.rt.get_sbucket, -1)
        self.assertRaises(IndexError, self.rt.get_sbucket, 160)
        self.assertRaises(IndexError, self.rt.get_sbucket, 161)

    def test_complete_coverage(self):
        #TODO: ips_in_table
        self.assertEqual(self.rt.get_closest_rnodes(76, 8, False), [tc.CLIENT_NODE])
        log_distance = self.my_node.distance(tc.SERVER_NODE).log
        str(self.rt.get_sbucket(log_distance).main)
        repr(self.rt)
        
        self.assertTrue(Bucket(1, set()) != Bucket(2, set()))

        buckets = [Bucket(2, set()), Bucket(2, set())]
        buckets[0].add(tc.CLIENT_NODE.get_rnode(1))
        buckets[1].add(tc.CLIENT_NODE.get_rnode(1))
        buckets[0].add(tc.NODES[0].get_rnode(1))
        buckets[1].add(tc.NODES[1].get_rnode(1))
        self.assertTrue(buckets[0] != buckets[1])

        self.assertEqual(buckets[0].get_freshest_rnode(), tc.NODES[0])
        stalest_rnode = buckets[0].get_stalest_rnode()
        self.assertEqual(stalest_rnode, tc.CLIENT_NODE)
        # Dangerous!!!
        stalest_rnode.last_seen = time.time()
        self.assertEqual(buckets[0].get_freshest_rnode(), tc.CLIENT_NODE)
            
        self.assertEqual(self.rt.find_next_bucket_with_room_index(tc.CLIENT_NODE), 0)
        self.assertEqual(self.rt.find_next_bucket_with_room_index(log_distance=6), 7)
        self.assertEqual(self.rt.find_next_bucket_with_room_index(log_distance=106), 107)

        self.rt.print_stats()


if __name__ == '__main__':
    main()
