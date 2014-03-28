# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import sys, os
import SocketServer

import core.ptime as time
import core.identifier as identifier



MIN_BT_PORT = 1024
MAX_BT_PORT = 2**16


class SanitizeError(Exception):
    pass

stop_server = False
dht = None

class Telnet(object):

    def __init__(self, dht_, port):
        global dht
        dht = dht_
        self.dht = dht
        self.port = port
        self.server = SocketServer.TCPServer(('', port), SessionHandler)

    def start(self):
        while not stop_server:
            self.server.handle_request()

            
class SessionHandler(SocketServer.StreamRequestHandler):

    def __init__(self, *args, **kwargs):
        self.open_channels = Channels()
        SocketServer.StreamRequestHandler.__init__(self, *args, **kwargs)
        
    def _on_peers_found(self, channel, peers, node):
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
        new_peers = []
        for peer in peers:
            if peer not in channel.peers:
                channel.peers.add(peer)
                new_peers.append(peer)
        for peer in new_peers:
            msg = '%d PEER %s:%d\r\n' % (channel.send,
                                         peer[0], peer[1])
            self.wfile.write(msg)
        return

    def _on_new_channel(self, splitted_line):
        if (len(splitted_line) != 6 or
            splitted_line[1] != 'OPEN' or
            splitted_line[3] != 'HASH'):
            raise SanitizeError, '? Invalid OPEN message'
        try:
            send = int(splitted_line[2])
        except (ValueError):
            raise SanitizeError, '? Channel must be integer'
        key, port_str = splitted_line[4:]
        try:
            info_hash = identifier.Id(key)
        except (identifier.IdError):
            raise SanitizeError, '? Invalid key (must be 40 HEX characters)'
        # if lookup_mode not in ('SLOW', 'FAST'):
        #     raise SanitizeError, '? Only FAST and SLOW lookup supported'
        try:
            port = int(port_str)
        except (ValueError):
            raise SanitizeError, '? Port must be integer'
        if port > MAX_BT_PORT:
            raise SanitizeError, '? Invalid port number'

        channel = self.open_channels.create(send)
        self.wfile.write('%d OPEN %d\r\n' % (channel.send, channel.recv))
        success = dht.get_peers(channel, info_hash,
                                self._on_peers_found, port)
        if 0:#not success:
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
        global stop_server
        while not stop_server:
            line = self.rfile.readline().strip().upper()
            if line == 'KILL':
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

