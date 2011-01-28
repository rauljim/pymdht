# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

from nose.tools import ok_, eq_

import sys
import logging

import ptime as time
import node
import identifier
import message
from message import Datagram
import minitwisted
import test_const as tc

import querier
from querier import Query, Querier
import logging_conf

logging_conf.testing_setup(__name__)
logger = logging.getLogger('dht')

import random
if random.random() > .8:
    RUN_CPU_INTENSIVE_TESTS = True
    print >>sys.stderr, '>>>>>>>>> Running cpu intensive tests in test_querier'
else:
    RUN_CPU_INTENSIVE_TESTS = False
    
TIMEOUT_DELAY = 3
LOOKUP_OBJ = 1

#TODO: get rid of Task()
class _TestQuery:

    def setup(self):
        time.mock_mode()
        
    def test_ping_with_response(self):
        # Client creates a query
        ping_msg = message.OutgoingPingQuery(tc.CLIENT_ID)
        q = Query(ping_msg, tc.SERVER_NODE)
        # Querier.register_query sets a TID and timeout_task
        q.tid = tc.TID
        q.timeout_task = minitwisted.Task(TIMEOUT_DELAY, None)
        q.query_ts = time.time()
        # The query is sent
        time.sleep(1)
        # The server creates a response
        ping_r_msg_out = message.OutgoingPingResponse(tc.SERVER_ID)
        bencoded_r = ping_r_msg_out.encode(tc.TID)
        # The client receives the bencoded message
        ping_r_in = message.IncomingMsg(
            Datagram(bencoded_r, tc.SERVER_ADDR))
        q.on_response_received(ping_r_in)
        assert 1 < q.rtt < 1.1
        assert q.lookup_obj is None
    
    def test_get_peers_with_response(self):
        # Client creates a query
        fn_msg = message.OutgoingGetPeersQuery(tc.CLIENT_ID,
                                               tc.INFO_HASH)
        # the destination's ID is unknown
        # This query belongs to a lookup
        q = Query(fn_msg, node.Node(tc.SERVER_ADDR), LOOKUP_OBJ)
        # Querier.register_query sets a TID and timeout_task
        q.tid = tc.TID
        q.timeout_task = minitwisted.Task(TIMEOUT_DELAY, None)
        q.query_ts = time.time()
        # The query is sent
        # The server creates a response
        fn_r_out = message.OutgoingGetPeersResponse(tc.SERVER_ID,
                                                    nodes=tc.NODES)
        bencoded_fn_r = fn_r_out.encode(tc.TID)
        time.sleep(1)
        # The client receives the bencoded message
        fn_r_in = message.IncomingMsg(
            Datagram(bencoded_fn_r, tc.SERVER_ADDR))
        q.on_response_received(fn_r_in)
        assert 1 < q.rtt < 1.1
        assert q.lookup_obj is LOOKUP_OBJ

    def test_find_node_with_error(self):
        # Client creates a query
        fn_msg = message.OutgoingFindNodeQuery(tc.CLIENT_ID,
                                               tc.TARGET_ID)
        # the destination's ID is unknown
        q = Query(fn_msg, node.Node(tc.SERVER_ADDR))
        # Querier.register_query sets a TID and timeout_task
        q.tid = tc.TID
        q.timeout_task = minitwisted.Task(TIMEOUT_DELAY, None)
        q.query_ts = time.time()
        # The query is sent
        # The server creates a response
        fn_r_out = message.OutgoingErrorMsg(message.GENERIC_E)
        bencoded_fn_r = fn_r_out.encode(tc.TID)
        time.sleep(1)
        # The client receives the bencoded message
        fn_r_in = message.IncomingMsg(
            Datagram(bencoded_fn_r, tc.SERVER_ADDR))
        q.on_error_received(fn_r_in)
        assert 1 < q.rtt < 1.1
        assert q.lookup_obj is None

    def teardown(self):
        time.normal_mode()

class TestQuerier:

    def setup(self):
        time.mock_mode()
        self.querier = Querier()#tc.CLIENT_ID)

    def test_generate_tids(self):
        #TODO: move to message
        if RUN_CPU_INTENSIVE_TESTS:
            num_tids =  pow(2, 16) + 2 #CPU intensive
        else:
            num_tids = 1000
        for i in xrange(num_tids):
            eq_(self.querier._next_tid(),
                chr(i%256)+chr((i/256)%256))

    def test_ping_with_reponse(self):
        # Client creates a query
        ping_msg = message.OutgoingPingQuery(tc.CLIENT_ID)
        q = Query(ping_msg, tc.SERVER_NODE)
        # Client registers query
        timeout_ts, bencoded_msgs = self.querier.register_queries([q])
        # Client sends bencoded_msg
        # Server gets bencoded_msg and creates response
        ping_r_msg_out = message.OutgoingPingResponse(tc.SERVER_ID)
        bencoded_r = ping_r_msg_out.stamp(ping_msg.tid, tc.CLIENT_NODE)
        time.sleep(1)
        ok_(not self.querier.get_timeout_queries())
        # The client receives the bencoded message (after 1 second)
        ping_r_in = message.IncomingMsg(
            Datagram(bencoded_r, tc.SERVER_ADDR))
        related_query = self.querier.on_response_received(ping_r_in)
        assert related_query is ping_msg

    def test_ping_with_timeout(self):
        # Client creates a query
        ping_msg = message.OutgoingPingQuery(tc.CLIENT_ID)
        q = Query(ping_msg, tc.SERVER_NODE)
        # Client registers query
        bencoded_msg = self.querier.register_queries([q])
        # Client sends bencoded_msg
        time.sleep(3)
        # The server never responds and the timeout is triggered
        timeout_queries = self.querier.get_timeout_queries()
        eq_(len(timeout_queries), 1)
        assert timeout_queries[0] is ping_msg

    def test_unsolicited_response(self):
        # Server creates unsolicited response
        # It might well be that the server responds using another port,
        # and therefore, the addr is not matched
        # TODO: consider accepting responses from a different port
        ping_r_msg_out = message.OutgoingPingResponse(tc.SERVER_ID)
        bencoded_r = ping_r_msg_out.stamp('zz', tc.CLIENT_NODE)
        # The client receives the bencoded message
        ping_r_in = message.IncomingMsg(
                Datagram(bencoded_r, tc.SERVER_ADDR))
        related_query = self.querier.on_response_received(ping_r_in)
        assert related_query is None

    def test_response_with_different_tid(self):
        # Client creates a query
        ping_msg = message.OutgoingPingQuery(tc.CLIENT_ID)
        q = Query(ping_msg, tc.SERVER_NODE)
        # Client registers query
        bencoded_msg = self.querier.register_queries([q])
        # Client sends bencoded_msg
        time.sleep(1)
        # Server gets bencoded_msg and creates response
        ping_r_msg_out = message.OutgoingPingResponse(tc.SERVER_ID)
        bencoded_r = ping_r_msg_out.stamp('zz', tc.CLIENT_NODE)
        # The client receives the bencoded message
        ping_r_in = message.IncomingMsg(
                    Datagram(bencoded_r, tc.SERVER_ADDR))
        related_query = self.querier.on_response_received(ping_r_in)
        assert related_query is None
        
    def test_error_received(self):
        # Client creates a query
        msg = message.OutgoingPingQuery(tc.CLIENT_ID)
        q = Query(msg, tc.SERVER_NODE)
        # Client registers query
        bencoded_msg = self.querier.register_queries([q])
        # Client sends bencoded_msg
        time.sleep(1)
        # Server gets bencoded_msg and creates response
        ping_r_msg_out = message.OutgoingErrorMsg(message.GENERIC_E)
        bencoded_r = ping_r_msg_out.stamp(msg.tid, tc.CLIENT_NODE)
        # The client receives the bencoded message
        ping_r_in = message.IncomingMsg(
                    Datagram(bencoded_r, tc.SERVER_ADDR))
        related_query = self.querier.on_error_received(ping_r_in)
        assert related_query is msg

    def test_many_queries(self):
        # Client creates a query
        msgs = [message.OutgoingPingQuery(tc.CLIENT_ID
                         ) for i in xrange(10)]
        queries = [Query(msg, tc.SERVER_NODE) for msg in msgs]
        # Client registers query
        bencoded_msg = self.querier.register_queries(queries)
        # Client sends bencoded_msg
        time.sleep(1)
        # response for queries[3]
        ping_r_msg_out = message.OutgoingPingResponse(tc.SERVER_ID)
        bencoded_r = ping_r_msg_out.stamp(msgs[3].tid, tc.CLIENT_NODE)
        ping_r_in = message.IncomingMsg(
                        Datagram(bencoded_r, tc.SERVER_ADDR))
        related_query = self.querier.on_response_received(ping_r_in)
        assert related_query is msgs[3]
        # error for queries[2]
        ping_r_msg_out = message.OutgoingErrorMsg(message.GENERIC_E)
        bencoded_r = ping_r_msg_out.stamp(msgs[2].tid, tc.CLIENT_NODE)
        ping_r_in = message.IncomingMsg(
                        Datagram(bencoded_r, tc.SERVER_ADDR))
        related_query = self.querier.on_error_received(ping_r_in)
        assert related_query is msgs[2]
        # response to wrong addr
        ping_r_msg_out = message.OutgoingPingResponse(tc.SERVER_ID)
        bencoded_r = ping_r_msg_out.stamp(msgs[5].tid, tc.CLIENT_NODE)
        ping_r_in = message.IncomingMsg(
                        Datagram(bencoded_r, tc.SERVER2_ADDR))
        related_query = self.querier.on_response_received(ping_r_in)
        assert related_query is None
        # response with wrong tid
        ping_r_msg_out = message.OutgoingPingResponse(tc.SERVER_ID)
        bencoded_r = ping_r_msg_out.stamp('ZZ', tc.CLIENT_NODE)
        ping_r_in = message.IncomingMsg(
                        Datagram(bencoded_r, tc.SERVER_ADDR))
        related_query = self.querier.on_response_received(ping_r_in)
        assert related_query is None
        # Still no time to trigger timeouts
        ok_(not self.querier.get_timeout_queries())
        time.sleep(1)
        # Now, the timeouts can be triggered
        timeout_queries = self.querier.get_timeout_queries()
        expected_msgs = msgs[:2] + msgs[4:]
        eq_(len(timeout_queries), len(expected_msgs))
        for related_query, expected_msg in zip(
            timeout_queries, expected_msgs):
            assert related_query is expected_msg

    def teardown(self):
        time.normal_mode()

