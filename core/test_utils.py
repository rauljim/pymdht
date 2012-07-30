# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

from unittest import TestCase, main

import utils


class TestUtils(TestCase):

    def test_compact_addr(self):
        cases = ((('1.2.3.4', 255), (1,2,3,4,0,255)),
                 (('199.2.3.4', 256), (199,2,3,4,1,0)),
                 )
        for case in cases:
            expected = ''.join([chr(i) for i in case[1]])
            self.assertEqual(utils.compact_addr(case[0]), expected)
                

if __name__ == '__main__':
    main()
