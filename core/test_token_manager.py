# Copyright (C) 2009-2010 Raul Jimenez, Flutra Osmani
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

from unittest import TestCase, main

import token_manager


IPS = ['1.1.1.1', '2.2.2.2']

class TestTokenManager(TestCase):

    def setUp(self):
        self.token_m1 = token_manager.TokenManager()
        self.token_m2 = token_manager.TokenManager()

    def test_get_token(self):
        self.assertEqual(self.token_m1.get(IPS[0]), self.token_m1.get(IPS[0]))
        self.assertEqual(self.token_m2.get(IPS[0]), self.token_m2.get(IPS[0]))
        self.assertTrue(self.token_m1.get(IPS[0]) != self.token_m2.get(IPS[0]))
        self.assertTrue(self.token_m1.get(IPS[0]) != self.token_m1.get(IPS[1]))
        self.assertTrue(self.token_m2.get(IPS[0]) != self.token_m2.get(IPS[1]))

    def test_check_token(self):
        for ip in IPS:
            self.assertTrue(self.token_m1.check(ip, self.token_m1.get(ip)))
            self.assertTrue(self.token_m2.check(ip, self.token_m2.get(ip)))
            self.assertTrue(not self.token_m1.check(ip, self.token_m2.get(ip)))
            self.assertTrue(not self.token_m2.check(ip, self.token_m1.get(ip)))


if __name__ == '__main__':
    main()
