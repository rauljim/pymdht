#! /usr/bin/env python

# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import SocketServer
import random
import sys, os
import socket
from optparse import OptionParser

import core.ptime as time
import logging
import core.logging_conf as logging_conf

#default_logs_level = logging.DEBUG # This generates HUGE (and useful) logs
#default_logs_level = logging.INFO # This generates some (useful) logs
#default_logs_level = logging.WARNING # This generates warning and error logs
default_logs_level = logging.ERROR # Just error logs

import core.identifier as identifier
import core.pymdht as pymdht

MAX_PORT = 2**16 - 1
#SCORING_PERIOD = 2 #0.2

NUM_PEERS_PER_BURST = 10

dht = None
stop_server = False
random_lookup_delay = 0

class SanitizeError(Exception):
    pass

class Channel(object):

    def __init__(self, send, recv):
        self.send = send
        self.recv = recv
        self.peers = set()
        self.open = True

class Channels(object):

    def __init__(self):
        self.channels = []
        self.next_recv = 1

    def create(self, send):
        recv = self.next_recv
        self.next_recv += 1
        channel = Channel(send, recv)
        self.channels.append(channel)
        return channel
        
    def get(self, recv):
        for channel in self.channels:
            if channel.recv == recv:
                return channel

    def remove(self, channel):
        recv = channel.recv
        for i in range(len(self.channels)):
            if self.channels[i].recv == recv:
                del self.channels[i]

                
class SessionHandler(SocketServer.StreamRequestHandler):

    def __init__(self, *args, **kwargs):
        self.open_channels = Channels()
        SocketServer.StreamRequestHandler.__init__(self, *args, **kwargs)
        
    def _on_peers_found(self, channel, peers):
        #current_time = time.time()
        if not channel.open:
            print 'Got peers but channel is CLOSED'
            return
        if not peers:
            print "end of lookup"
            self.open_channels.remove(channel)
            self.wfile.write('%d CLOSE\r\n' % (channel.send))
            return
        print 'got %d peer' % len(peers)
        scored_peers = []
        for peer in peers:
            if peer not in channel.peers:
                channel.peers.add(peer)
                if geo_score:
                    peer_score = geo_score.score_peer(peer[0])
                else:
                    peer_score = 0
                scored_peers.append((peer, peer_score))

        if geo_score:
            sorted_scored_peers = sorted(scored_peers, key = lambda elem:elem[1])
            #TODO: is the top 10 OK?
            sorted_scored_peers = sorted_scored_peers[:NUM_PEERS_PER_BURST]
        else:
            sorted_scored_peers = scored_peers
        for peer, score in sorted_scored_peers:
            msg = '%d PEER %s:%d SCORE %d\r\n' % (channel.send,
                                                       peer[0], peer[1],
                                                       score)
            self.wfile.write(msg)
        return

    def _on_new_channel(self, splitted_line):
        if (len(splitted_line) != 7 or
            splitted_line[1] != 'OPEN' or
            splitted_line[3] != 'HASH'):
            raise SanitizeError, '? Invalid OPEN message'
        try:
            send = int(splitted_line[2])
        except (ValueError):
            raise SanitizeError, '? Channel must be integer'
        key, lookup_mode, port_str = splitted_line[4:]
        try:
            info_hash = identifier.Id(key)
        except (identifier.IdError):
            raise SanitizeError, '? Invalid key (must be 40 HEX characters)'
        if lookup_mode not in ('SLOW', 'FAST'):
            raise SanitizeError, '? Only FAST and SLOW lookup supported'
        try:
            port = int(port_str)
        except (ValueError):
            raise SanitizeError, '? Port must be integer'
        if port > MAX_PORT:
            raise SanitizeError, '? Invalid port number'

        channel = self.open_channels.create(send)
        self.wfile.write('%d OPEN %d\r\n' % (channel.send, channel.recv))
        success = dht.get_peers(channel, info_hash,
                                self._on_peers_found, port)
        # if peers:
        #     for peer in peers:
        #         if peer not in channel.peers:
        #             channel.peers.add(peer)
        #             peer_score = geo_score.score_peer(peer[0])
        #             self.wfile.write('%d PEER %s:%d SCORE %d\r\n' % (channel.send,
        #                                                              peer[0], peer[1],
        #                                                              peer_score))
        if not success:
            print 'no success'
            self.open_channels.remove(channel)
            self.wfile.write('%d CLOSE\r\n' % (channel.send))
        

    def _on_existing_channel(self, recv, splitted_line):
        channel = self.open_channels.get(recv)
        if not channel:
            raise SanitizeError, '? Wrong channel'
        if (len(splitted_line) != 2 or
            splitted_line[1] != 'CLOSE'):
            raise SanitizeError, '%d Only CLOSE is accepted' % (
                channel.send)
        channel.open = False
        self.open_channels.remove(channel)
        self.wfile.write('%d CLOSE\r\n' % (channel.send))
    
    def _get_recv(self, splitted_line):
        if not splitted_line: 
            raise SanitizeError, "? I don't like empty lines"
        try:
            return int(splitted_line[0])
        except (ValueError):
            raise SanitizeError, '? Channel must be a number'
    
    def handle(self):
        while not stop_server:
            line = self.rfile.readline().strip().upper()
            if line == 'KILL':
                global stop_server
                stop_server = True
                return
            if line == 'CRASH':
                dht.stop()
                continue
            if line == 'EXIT':
                return
            splitted_line = line.split()
            try:
                recv = self._get_recv(splitted_line)
                if recv:
                    response = self._on_existing_channel(recv, splitted_line)
                else:
                    response = self._on_new_channel(splitted_line)
            except (SanitizeError), error_msg:
                self.wfile.write('%s\r\n' % (error_msg))

                
def main(options, args):
    port = int(options.port)
    my_addr = (options.ip, port)
    if not os.path.isdir(options.path):
        if os.path.exists(options.path):
            print 'FATAL:', options.path, 'must be a directory'
            return
        print options.path, 'does not exist. Creating directory...'
        os.mkdir(options.path)
    logs_path = options.path
    logs_level = options.logs_level or default_logs_level
    logging_conf.setup(logs_path, logs_level)
    print 'Using the following plug-ins:'
    print '*', options.routing_m_file
    print '*', options.lookup_m_file
    print 'Path:', options.path
    print 'Private DHT name:', options.private_dht_name
    routing_m_name = '.'.join(os.path.split(options.routing_m_file))[:-3]
    routing_m_mod = __import__(routing_m_name, fromlist=[''])
    lookup_m_name = '.'.join(os.path.split(options.lookup_m_file))[:-3]
    lookup_m_mod = __import__(lookup_m_name, fromlist=[''])
    exp_m_name = '.'.join(os.path.split(options.exp_m_file))[:-3]
    exp_m_mod = __import__(exp_m_name, fromlist=[''])

    global dht
    dht = pymdht.Pymdht(my_addr, logs_path,
                        routing_m_mod,
                        lookup_m_mod,
                        exp_m_mod,
                        options.private_dht_name,
                        logs_level)

    random_lookup_delay = options.random_lookup_delay
    while random_lookup_delay > 0:
        time.sleep(float(random_lookup_delay))
        target = identifier.RandomId()
        dht.get_peers(None, target, None, 0)

    
    global geo_score
    if options.geoip_mode:
        try:
            import geo
            geo_score = geo.Geo(local_ip)
        except:
            print "---------------------------------------"
            print "Geo module FAILED: you cannot use --geo"
            print "---------------------------------------"
            raise
    else:
        geo_score = None
    
    global server
    server = SocketServer.TCPServer(('', port), SessionHandler)
    while not stop_server:
        server.handle_request()
    
        
if __name__ == '__main__':
    default_path = os.path.join(os.path.expanduser('~'), '.pymdht')
    parser = OptionParser()

    #get IP address of the local computer
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('google.com', 80))
    local_ip = s.getsockname()[0]
    del s
    
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
    parser.add_option("-e", "--exp-plug-in", dest="exp_m_file",
                      metavar='FILE', default='core/exp_plugin_template.py',
                      help="file containing the experiment_manager code")
    parser.add_option("-z", "--logs-level", dest="logs_level",
                      metavar='INT', default=0,
                      help="logging level")
    parser.add_option("-d", "--private-dht", dest="private_dht_name",
                      metavar='STRING', default=None,
                      help="private DHT name")
    parser.add_option("-m", "--my-address", dest="my_ip",
                      metavar='IP', default=local_ip,
                      help="local IP address")
    parser.add_option("--geoip", dest="geoip_mode",
                      action='store_true', default=False,
                      help="do not use geoIP")
    parser.add_option("--random-lookup", dest="random_lookup_delay",
                      metavar='INT', default=0,
                      help="Perform lookups (to random keys) every x seconds")


    (options, args) = parser.parse_args()
    
    '''
    # Trace memory leaks
    import cherrypy
    import dowser
    cherrypy.config.update({'server.socket_port': 8080})
    cherrypy.tree.mount(dowser.Root())
    cherrypy.engine.start()
    '''
    main(options, args)


