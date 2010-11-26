# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import logging

from nose.tools import ok_, eq_

import ptime as time
import test_const as tc
import message
import querier

import controller

import routing_plugin_template as routing_m_mod
import lookup_plugin_template as lookup_m_mod

import logging_conf
logging_conf.testing_setup(__name__)
logger = logging.getLogger('dht')


def assert_almost_equal(result, expected, tolerance=.01):
    if not expected-tolerance < result < expected+tolerance:
        assert False, 'result: %f, expected: %f' % (result,
                                                    expected)

class TestController:

    def setup(self):
        self.controller = controller.Controller(tc.CLIENT_ADDR, 'test_logs',
                                                routing_m_mod,
                                                lookup_m_mod,
                                                None)
        self.my_id = self.controller._my_id
        self.querier2 = querier.Querier(self.my_id)

    def _test_start_stop(self):
        self.controller.main_loop()

    def test_load_save_state(self):
        #TODO: change state
        self.controller.save_state()
        #TODO:check file
        self.controller.load_state()
        #TODO: check state

    def test_simple(self):
        q = querier.Query(message.OutgoingPingQuery(self.my_id),
                          tc.SERVER_NODE)
        expected_ts, expected_msgs = self.querier2.register_queries([q])
        ts, msgs = self.controller.main_loop()
        assert_almost_equal(ts, expected_ts)
        eq_(len(msgs), 1)
        eq_(msgs[0], expected_msgs[0])

    def test_adding_and_removing_node(self):
        # The routing table is initially empty
        eq_(self.controller._routing_m.get_main_rnodes(), [])

        q = querier.Query(message.OutgoingPingQuery(self.my_id),
                          tc.SERVER_NODE)
        expected_ts, expected_msgs = self.querier2.register_queries([q])
        # main_loop is called by reactor.start()
        # It returns a maintenance ping
        ts, msgs = self.controller.main_loop()
        assert_almost_equal(ts, expected_ts)
        eq_(len(msgs), 1)
        eq_(msgs[0], expected_msgs[0])
        time.sleep((ts - time.time()) / 2)
        # SERVER_NODE replies before the timeout
        tid = message.IncomingMsg(msgs[0][0], tc.CLIENT_ADDR).tid
        datagram = message.OutgoingPingResponse(tc.SERVER_ID).encode(tid)
        eq_(self.controller._routing_m.get_main_rnodes(), [])
        self.controller.on_datagram_received(datagram, tc.SERVER_ADDR)
        # SERVER_NODE is added to the routing table
        eq_(self.controller._routing_m.get_main_rnodes(), [tc.SERVER_NODE])

        time.sleep((ts - time.time()))
        # main_loop is called to trigger timeout
        # It returns a maintenance lookup
        ts, msgs = self.controller.main_loop() 
        q = querier.Query(message.OutgoingFindNodeQuery(self.my_id,
                                                        self.my_id),
                          tc.SERVER_NODE)
        expected_ts, expected_msgs = self.querier2.register_queries([q])
        assert_almost_equal(ts, expected_ts)
        eq_(len(msgs), 1)
        eq_(msgs[0], expected_msgs[0])
        
        time.sleep(ts - time.time())
        # main_loop is called to trigger timeout
        # It triggers a timeout (removing SERVER_NODE from the routing table
        # returns a maintenance ping
        ts, msgs = self.controller.main_loop()
        eq_(self.controller._routing_m.get_main_rnodes(), [])
        # No reply for this query
        #this call should trigger timeout
        self.controller.main_loop()

    def _test_get_peers(self):
        ts, msgs = self.controller.get_peers(None, tc.INFO_HASH, None, 0)
        assert_almost_equal(ts, time.time(), 2)
        eq_(msgs, [])

    def _test_complete(self):
        # controller.start() starts reactor (we don't want to use reactor in
        # tests), sets _running, and calls main_loop
        self.controller._running = True
        # controller.start calls main_loop, which does maintenance (bootstrap)
        self.controller.main_loop()
        # minitwisted informs of a response
        data = message.OutgoingPingResponse(tc.SERVER_ID).encode('\0\0')
        self.controller.on_datagram_received(data, tc.SERVER_ADDR)
        self.controller.main_loop() # maintenance (maintenance lookup)
        
    def tear_down(self):
        pass
