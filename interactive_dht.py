#! /usr/bin/env python

# Copyright (C) 2009-2011 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import core.ptime as time
import sys, os
from optparse import OptionParser

import logging
import core.logging_conf as logging_conf

logs_level = logging.DEBUG # This generates HUGE (and useful) logs
#logs_level = logging.INFO # This generates some (useful) logs
#logs_level = logging.WARNING # This generates warning and error logs

import core.identifier as identifier
import core.pymdht as pymdht


def main(options, args):
    my_addr = (options.ip, int(options.port))
    if not os.path.isdir(options.path):
        if os.path.exists(options.path):
            print 'FATAL:', options.path, 'must be a directory'
            return
        print options.path, 'does not exist. Creating directory...'
        os.mkdir(options.path)
    logs_path = options.path
    
    print 'Using the following plug-ins:'
    print '*', options.routing_m_file
    print '*', options.lookup_m_file
    print '*', options.experimental_m_file
    print 'Path:', options.path
    print 'Private DHT name:', options.private_dht_name
    routing_m_name = '.'.join(os.path.split(options.routing_m_file))[:-3]
    routing_m_mod = __import__(routing_m_name, fromlist=[''])
    lookup_m_name = '.'.join(os.path.split(options.lookup_m_file))[:-3]
    lookup_m_mod = __import__(lookup_m_name, fromlist=[''])
    experimental_m_name = '.'.join(os.path.split(options.experimental_m_file))[:-3]
    experimental_m_mod = __import__(experimental_m_name, fromlist=[''])
    

    dht = pymdht.Pymdht(my_addr, logs_path,
                        routing_m_mod,
                        lookup_m_mod,
                        experimental_m_mod,
                        options.private_dht_name,
                        logs_level)
    if options.gui:
        import wx
        import ui.gui
        app = wx.PySimpleApp()
        frame = ui.gui.Interactive_GUI(None, "Interactive DHT . . .", None,(1440,900), dht)
        frame.Show(True)
        app.MainLoop()
    elif options.cli:
        import ui.cli
        ui.cli.command_user_interface(dht)
        
if __name__ == '__main__':
    default_path = os.path.join(os.path.expanduser('~'), '.pymdht')
    parser = OptionParser()
    parser.add_option("-a", "--address", dest="ip",
                      metavar='IP', default='127.0.0.1',
                      help="IP address to be used")
    parser.add_option("-p", "--port", dest="port",
                      metavar='INT', default=7000,
                      help="port to be used")
    parser.add_option("-x", "--path", dest="path",
                      metavar='PATH', default=default_path,
                      help="state.dat and logs location")
    parser.add_option("-r", "--routing-plug-in", dest="routing_m_file",
                      metavar='FILE', default='plugins/routing_nice_rtt.py',
                      help="file containing the routing_manager code")
    parser.add_option("-l", "--lookup-plug-in", dest="lookup_m_file",
                      metavar='FILE', default='plugins/lookup_a4.py',
                      help="file containing the lookup_manager code")
    parser.add_option("-z", "--logs-level", dest="logs_level",
                      metavar='INT',
                      help="logging level")
    parser.add_option("-d", "--private-dht", dest="private_dht_name",
                      metavar='STRING', default=None,
                      help="private DHT name")
    parser.add_option("-e", "--experimental-plug-in",dest="experimental_m_file",
                      metavar='FILE', default='core/exp_plugin_template.py',
                      help="file containing ping-manager code")
    parser.add_option("--debug",dest="debug",
                      action='store_true', default=False,
                      help="DEBUG mode")
    parser.add_option("--gui",dest="gui",
                      action='store_true', default=False,
                      help="Graphical user interface")
    parser.add_option("--cli",dest="cli",
                      action='store_true', default=True,
                      help="Command line interface (no GUI) <- default")
    parser.add_option("--daemon", dest="daemon",
                      action='store_true', default=False,
                      help="DAEMON mode (no interface)")
    parser.add_option("--telnet",dest="telnet",
                      action='store_true', default=False,
                      help="Telnet interface (only on DAEMON mode)")

    (options, args) = parser.parse_args()
    
#    if option.telnet and not option.daemon:
#        print 'FATAL: telnet interfate only works on DAEMON mode'
        #return
    main(options, args)


