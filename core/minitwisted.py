# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

'''
Minitwisted is inspired by the Twisted framework. Although, it is much
simpler.
- It can only handle one UDP connection per reactor.
- Reactor runs in a thread
- You can use call_later and call_now to run your code in thread-safe mode

'''

import sys
import socket
import threading
import logging

import ptime as time
from floodbarrier import FloodBarrier

logger = logging.getLogger('dht')

BUFFER_SIZE = 3000

                            
class ThreadedReactor(threading.Thread):

    """
    Object inspired in Twisted's reactor.
    Run in its own thread.
    It is an instance, not a nasty global
    
    """
    def __init__(self, main_loop_f,
                 port, on_datagram_received_f,
                 task_interval=0.1,
                 floodbarrier_active=True):
        threading.Thread.__init__(self)
        self.daemon = True
        
        self._lock = threading.RLock()
        self._running = False
        self._call_asap_queue = []
        self._next_main_loop_call_ts = 0 # call immediately

        self._main_loop_f = main_loop_f
        self._port = port
        self._on_datagram_received_f = on_datagram_received_f
        self.task_interval = task_interval
        self.floodbarrier_active = floodbarrier_active
        if self.floodbarrier_active:
            self.floodbarrier = FloodBarrier()

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.settimeout(self.task_interval)
        my_addr = ('', self._port)
        self.s.bind(my_addr)

    def _get_running(self):
        self._lock.acquire()
        try:
            running = self._running
        finally:
            self._lock.release()
        return running

    def _set_running(self, running):
        self._lock.acquire()
        try:
            self._running = running
        finally:
            self._lock.release()
    running = property(_get_running, _set_running)

    def run(self):
        self.running = True
        logger.critical('run')
        try:
            while self.running:
                self._protected_run()
        except:
            logger.critical( 'MINITWISTED CRASHED')
            logger.exception('MINITWISTED CRASHED')
        self.running = False
        logger.debug('Reactor stopped')

    def _protected_run(self):
        """Main loop activated by calling self.start()"""

        # Deal with call_asap requests
        #TODO: retry for 5 seconds if no msgs_to_send (inside controller?)
        call_asap_tuple = None
        self._lock.acquire()
        try:
            if self._call_asap_queue:
                call_asap_tuple = self._call_asap_queue.pop(0)
        finally:
            self._lock.release()
        if call_asap_tuple:
            callback_f, args, kwds = call_asap_tuple
            (self._next_main_loop_call_ts,
             msgs_to_send) = callback_f(*args, **kwds)
            for msg, addr in msgs_to_send:
                self._sendto(msg, addr)
                    
        # Call main_loop
        if time.time() > self._next_main_loop_call_ts:
            (self._next_main_loop_call_ts,
             msgs_to_send) = self._main_loop_f()
            for msg, addr in msgs_to_send:
                self._sendto(msg, addr)

        # Get data from the network
        try:
            data, addr = self.s.recvfrom(BUFFER_SIZE)
        except (socket.timeout):
            pass #timeout
        except (socket.error), e:
            logger.warning(
                'Got socket.error when receiving data:\n%s' % e)
        else:
            ip_is_blocked = self.floodbarrier_active and \
                            self.floodbarrier.ip_blocked(addr[0])
            if ip_is_blocked:
                logger.warning('%s blocked' % `addr`)
                return
            (self._next_main_loop_call_ts,
             msgs_to_send) = self._on_datagram_received_f(
                data, addr)
            for msg, addr in msgs_to_send:
                self._sendto(msg, addr)
            
    def stop(self):#, stop_callback):
        """Stop the thread. It cannot be resumed afterwards"""

        self.running = False
        self.join(self.task_interval*10)
        if self.isAlive():
            raise Exception, 'Minitwisted thread is still alive!'
        #TODO: stop_callback()

    def call_asap(self, callback_f, *args, **kwds):
        """Call the given callback with given arguments as soon as possible
        (next time _protected_run is called).
        
        """ 
        self._lock.acquire()
        try:
            self._call_asap_queue.append((callback_f, args, kwds))
        finally:
            self._lock.release()
        return
        
    def _sendto(self, data, addr):
        """Send data to addr using the UDP port used by listen_udp."""

        try:
            bytes_sent = self.s.sendto(data, addr)
            if bytes_sent != len(data):
                logger.warning(
                    'Just %d bytes sent out of %d (Data follows)' % (
                        bytes_sent, len(data)))
                logger.critical('Data: %s' % data)
        except (socket.error):
            logger.warning(
                'Got socket.error when sending data to %r\n%r' % (addr,
                                                                  data))

