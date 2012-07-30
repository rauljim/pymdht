# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import unittest
import logging

import test_const as tc

import pymdht

import lookup_plugin_template as lookup_m_mod

class TestPymdht(unittest.TestCase):

    def _callback(self, *args, **kwargs):
        return
    
    def setUp(self):
        self.dht = pymdht.Pymdht(tc.CLIENT_NODE, 'test_logs',
                                 None,#routing_m_mod,
                                 lookup_m_mod,
                                 None,#exp_m_mod,
                                 None, logging.DEBUG)

    def test_interface(self):
        #self.dht.start()
        self.dht.get_peers(None, tc.INFO_HASH, self._callback, tc.BT_PORT)
        self.dht.stop()


if __name__ == '__main__':
    unittest.main()
