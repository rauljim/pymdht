#! /usr/bin/env python

# Copyright (C) 2012 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import sys

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "usage: %d input" % (sys.argv[0])
    else:
        state_in = open(sys.argv[1], 'r')
        line = state_in.readline() # first line (node's ID)
        for line in state_in:
            _, _, _, ip, port, _, _ = line.split()
            print '%s %s' % (ip, port)
