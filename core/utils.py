# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import os
import sys
import socket
import logging

import node

logger = logging.getLogger('dht')

class AddrError(Exception):
    pass

class IP6Addr(AddrError):
    pass
#TODO2: IPv6 support


#TODO2: move binary functions from identifier

def compact_port(port):
    return ''.join(
        [chr(port_byte_int) for port_byte_int in divmod(port, 256)])

'''
def uncompact_port(c_port_net):
    return ord(bin_str[0]) * 256 + ord(bin_str[1])
'''

def compact_addr(addr):
    return socket.inet_aton(addr[0]) + compact_port(addr[1])
'''
def uncompact_addr(c_addr):
    try:
        return (socket.inet_ntoa(c_addr[:-2],
                                 uncompact_port(c_addr[-2:])))
    except (socket.error):
        raise AddrError
'''
compact_peer = compact_addr

def get_subnet(addr):
    return socket.inet_aton(addr[0])[:3]
        

def get_open_file(filename, mode='r'):
    data_path = os.path.dirname(node.__file__)
    abs_filename = os.path.join(data_path, filename)
    
    # Arno, 2012-05-25: py2exe support
    if hasattr(sys, "frozen"):
        print >>sys.stderr,"pymdht: utils.py py2exe: Frozen mode"
        installdir = os.path.dirname(unicode(
                sys.executable,sys.getfilesystemencoding()))
        if sys.platform == "darwin":
            installdir = installdir.replace("MacOS","Resources")
        abs_filename = os.path.join(installdir, "Tribler", "Core",
                         "DecentralizedTracking", "pymdht", "core",
                         filename)
        print >>sys.stderr,"pymdht: utils.py py2exe:", filename, abs_filename
    try:
        return open(abs_filename, mode)
    except (IOError):
        logger.execption('Ignoring this file...')
