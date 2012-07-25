# Copyright (C) 2011 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information
"""
- main and backup bootstrap nodes
These nodes are hardcoded (see core/bootstrap.main and core/bootstrap.backup)
Main nodes are run by us, backup nodes are wild nodes we have seen running for
a long time.
Each bootstrap step, a number of main nodes and backup nodes (see
*_NODES_PER_BOOTSTRAP) are used to peroform a lookup.
These bootstrap nodes SHOULD NOT be added to the routing table to avoid
overloading them (use is_bootstrap_node() before adding nodes to routing table!
"""

import os
import sys
import random
import logging

import ptime as time
import identifier
import message
import node

logger = logging.getLogger('dht')

STABLE_FILENAME = 'bootstrap_stable'
UNSTABLE_FILENAME = 'bootstrap_unstable'
LOCAL_FILENAME = 'bootstrap_local' #TODO: ~/.pymdht

MAX_ADDRS = 2050


class OverlayBootstrapper(object):

    def __init__(self):
        #TODO: subnet
        self.hardcoded_ips = set()
        self._stable_ip_port = {}
        self._unstable_ip_port = {}

        filename = STABLE_FILENAME
        f = _get_open_file(filename)
        for line in f:
            addr = _sanitize_bootstrap_addr(line)
            self.hardcoded_ips.add(addr[0])
            self._stable_ip_port[addr[0]] = addr[1]
        print '%s: %d hardcoded, %d bootstrap' % (filename,
                                                  len(self.hardcoded_ips),
                                                  len(self._ip_port))
        filename = LOCAL_FILENAME
        f = _get_open_file(filename)
        local_exists = 
        for line in f:
            addr = _sanitize_bootstrap_addr(line)
            self._unstable_ip_port[addr[0]] = addr[1]
        print '%s: %d hardcoded, %d bootstrap' % (filename,
                                                  len(self.hardcoded_ips),
                                                  len(self._ip_port))
        filename = UNSTABLE_FILENAME
        f = _get_open_file(filename)
        for line in f:
            addr = _sanitize_bootstrap_addr(line)
            self.hardcoded_ips.add(addr[0])
        print '%s: %d hardcoded, %d bootstrap' % (filename,
                                                  len(self.hardcoded_ips),
                                                  len(self._ip_port))

    def get_sample_unstable_addrs(self, num_addrs):
        addrs = list(self._ip_port.items())
        addrs = random.sample(addrs, num_addrs)
        return addrs

    def get_shuffled_stable_addrs(self):
        addrs = 
        
    def is_hardcoded(self, addr):
        """
        Having addresses hardcoded increases the load of these nodes "lucky"
        enough to be in the list.
        To compensate, these nodes should not be added to the routing table.

        Routing manager should check a node before adding to routing table.
        """
        return addr[0] in self.hardcoded_ips

    def report_unreachable(self, addr):
        #remove from dict
        #TODO: do not remove if many unreachable reports in a row (node may be
        #temporarely offline (common in Android)
        self._unstable_ip_port.pop(addr[0], None)

    def report_reachable(self, addr, reachable_since=0):
        if addr[0] in self._stable_ip_port:
            # already in STABLE list, don't add to UNSTABLE
            return
        if reachable_since == 0:
            if len(self._ip_port) < MAX_ADDRS:
                self._unstable_ip_port[addr[0]] = addr[1]
        else:
            #TODO: save a long-term reachable node every hour
            pass

    def save_to_file():
        addrs = list(self._ip_port.items())
        addrs.sort()
        for addr in addrs:
            out = _get_open_file(BOOTSTRAP_LOCAL_FILENAME, 'w')
            print >>out, addr[0], addr[1] #TODO: inet_aton
        self._ip_port = {}
        

def _sanitize_bootstrap_addr(line):
    # no need to catch exceptions, get_bootstrap_nodes takes care of them
    ip, port_str = line.split()
    return ip, int(port_str)

def _get_open_file(filename, mode='r'): #TODO: move to utils
    data_path = os.path.dirname(message.__file__)
    abs_filename = os.path.join(data_path, filename)
    
    # Arno, 2012-05-25: py2exe support
    if hasattr(sys, "frozen"):
        print >>sys.stderr,"pymdht: bootstrap: Frozen mode"
        installdir = os.path.dirname(unicode(
                sys.executable,sys.getfilesystemencoding()))
        if sys.platform == "darwin":
            installdir = installdir.replace("MacOS","Resources")
        abs_filename = os.path.join(installdir, "Tribler", "Core",
                         "DecentralizedTracking", "pymdht", "core",
                         filename)
    print >>sys.stderr,"pymdht: bootstrap:", filename, abs_filename
    try:
        f = open(abs_filename, mode)
    except (IOError):
        f = []
    return f
