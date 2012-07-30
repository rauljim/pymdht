# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import logging

import unittest
from nose.tools import ok_, eq_

import ptime as time
import test_const as tc
import message
from message import Datagram
import querier
import identifier

import controller

import lookup_plugin_template as lookup_m_mod

import logging_conf
logging_conf.testing_setup(__name__)
logger = logging.getLogger('dht')

PYMDHT_VERSION = (11, 2, 3)
VERSION_LABEL = ''.join(
    ['NS',
     chr((PYMDHT_VERSION[0] - 11) * 24 + PYMDHT_VERSION[1]),
     chr(PYMDHT_VERSION[2])
     ])


def assert_almost_equal(result, expected, tolerance=.05):
    if not expected-tolerance < result < expected+tolerance:
        assert False, 'result: %f, expected: %f' % (result,
                                                    expected)

class TestController(unittest.TestCase):

    def setUp(self):
        time.mock_mode()
        
        self.controller = controller.Controller(VERSION_LABEL,
                                                tc.CLIENT_NODE,
                                                'test_logs',
                                                None,#routing_m_mod,
                                                lookup_m_mod,
                                                None,#exp_m_mod,
                                                None, False)
        self.my_id = self.controller._my_id
        self.querier2 = querier.Querier()#self.my_id)
        self.servers_msg_f = message.MsgFactory(VERSION_LABEL, tc.SERVER_ID)
        
    def _test_start_stop(self):
        self.controller.main_loop()

    def test_successful_get_peers(self):
        lookup_result = []
        datagrams = self.controller.get_peers(lookup_result, tc.INFO_HASH,
                                              lambda x,y,z: x.append(y), 0,
                                              False)
        #FIXME: eq_(len(lookup_result), 1) # the node is tracking this info_hash
        #FIXME: eq_(lookup_result[0][0], tc.CLIENT_ADDR)

    def test_bad_datagram_received(self):
        ts, datagrams = self.controller.on_datagram_received(
            message.Datagram('aa', tc.CLIENT_ADDR))
        assert not datagrams

    def test_query_received(self):
        #TODO
        pass

    def test_error_received(self):
        #TODO
        pass
        
    def _old(self):
        # controller.start() starts reactor (we don't want to use reactor in
        # tests), sets _running, and calls main_loop
        self.controller._running = True
        # controller.start calls main_loop, which does maintenance (bootstrap)
        self.controller.main_loop()
        # minitwisted informs of a response
        data = message.OutgoingPingResponse(tc.CLIENT_NODE,
                                            tc.SERVER_ID).stamp('\0\0')
        self.controller.on_datagram_received(
            message.Datagram(data, tc.SERVER_ADDR))
        self.controller.main_loop() # maintenance (maintenance lookup)
        
    def tearDown(self):
        time.normal_mode()


if __name__ == '__main__':
    unittest.main()
