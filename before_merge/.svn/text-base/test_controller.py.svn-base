# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import test_const as tc

import controller



class TestController:

    def setup(self):
        self.controller = controller.Controller(tc.CLIENT_ADDR, 'test_logs')

    def test_start_stop(self):
        self.controller.start()
        self.controller.stop()

    def test_load_save_state(self):
        #TODO: change state
        self.controller.save_state()
        #TODO:check file
        self.controller.load_state()
        #TODO: check state

    def test_get_peers(self):
        self.controller.start()
        self.controller.get_peers(tc.INFO_HASH, lambda x:None)
        self.controller.stop()
