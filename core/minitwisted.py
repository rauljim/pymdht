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

#from __future__ import with_statement

import sys
import socket
import threading
import ptime as time

import logging

from floodbarrier import FloodBarrier
from task_manager import Task, TaskManager

#from profilestats import profile

logger = logging.getLogger('dht')


BUFFER_SIZE = 3000

                            
class ThreadedReactor(threading.Thread):

    """
    Object inspired in Twisted's reactor.
    Run in its own thread.
    It is an instance, not a nasty global
    
    """
    def __init__(self, main_loop_f,
                 task_interval=0.1,
                 floodbarrier_active=True):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        
        self._running = False
        self._call_asap_queue = []
        self._lock = threading.RLock()

        self._main_loop_f = main_loop_f
        self.task_interval = task_interval
        self.floodbarrier_active = floodbarrier_active
        if self.floodbarrier_active:
            self.floodbarrier = FloodBarrier()

    #@profile
    def run(self):
        self.main_loop_f
        self._running = True
        try:
            while running:
                self._lock.acquire()
                try:
                    running = self._running
                finally:
                    self._lock.release()
                self._protected_run()
        except:
            logger.critical( 'MINITWISTED CRASHED')
            logger.exception('MINITWISTED CRASHED')
        self._lock.acquire()
        try:
            self._running = False
        finally:
            self._lock.release()
        print 'Reactor stopped!'
        logger.debug('Reactor stopped')

    def _protected_run(self):
        """Main loop activated by calling self.start()"""

        # Deal with call_asap requests
        while 1:
            #TODO: retry for 5 seconds if no msgs_to_send (inside controller?)
            self._lock.acquire()
            try:
                if self._running and self._call_asap_queue:
                    call_asap_tuple = self._call_asap_queue.pop(0)
            finally:
                self._lock.release()
            if call_asap_tuple:
                callback_f, args, kwds = call_asap_tuple
                (self._next_call_ts,
                 msgs_to_send) = callbac_f(*args, **kwds)
                for msg, addr in msgs_to_send:
                    self.sendto(msg, addr)
            else:
                break # no more asap calls to make
        
        # Call main_loop
        if time.time() > self._next_call_ts:
            (self._next_call_ts,
             msgs_to_send) = self._main_loop_f()
        for msg, addr in msgs_to_send:
            self.sendto(msg, addr)

        # Get data from the network
        try:
            data, addr = self.s.recvfrom(BUFFER_SIZE)
        except (socket.timeout):
            pass #timeout
        except (socket.error), e:
            logger.warning(
                'Got socket.error when receiving data:\n%s' % e)
            #logger.exception('See critical log above')
        else:
            ip_is_blocked = self.floodbarrier_active and \
                            self.floodbarrier.ip_blocked(addr[0])
            if ip_is_blocked:
                logger.warning('%s blocked' % `addr`)
                return
            (self._next_call_ts,
             msgs_to_send) = self.datagram_received_f(
                data, addr)
            for msg, addr in msgs_to_send:
                self.sendto(msg, addr)
            
    def stop(self):
        """Stop the thread. It cannot be resumed afterwards"""

        self._lock.acquire()
        try:
            self._runnig = False
        finally:
            self._lock.release()

    def listen_udp(self, port, datagram_received_f):
        """Listen on given port and call the given callback when data is
        received.

        """
        self.datagram_received_f = datagram_received_f
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.settimeout(self.task_interval)
        my_addr = ('', port)
        self.s.bind(my_addr)
        return self.s
        
    def call_asap(self, callback_f, *args, **kwds):
        """Call the given callback with given arguments as soon as possible
        (next time _protected_run is called).
        
        """ 
        self._get_peers_queue_lock.acquire()
        try:
            self._get_peers_queue.append((callback_f, args, kwds))
        finally:
            self._get_peers_queue_lock.release()
        return
        
    def sendto(self, data, addr):
        """Send data to addr using the UDP port used by listen_udp."""
        #with self._lock:
        self._lock.acquire()
        try:
            bytes_sent = self.s.sendto(data, addr)
            if bytes_sent != len(data):
                logger.critical(
                    'Just %d bytes sent out of %d (Data follows)' % (
                        bytes_sent,
                        len(data)))
                logger.critical('Data: %s' % data)
        except (socket.error):
            logger.warning(
                'Got socket.error when sending data to %r\n%r' % (addr,
                                                                  data))


class ThreadedReactorSocketError(ThreadedReactor):

    def listen_udp(self, delay, callback_f, *args, **kwds):
        self.s = _SocketMock()

                
class ___ThreadedReactorMock(object):
 
    def __init__(self, task_interval=0.1):
        pass
    
    def start(self):
        pass

    stop = start

    def listen_udp(self, port, data_received_f):
        self.s = _SocketMock()
        return self.s

    def call_later(self, delay, callback_f, *args, **kwds):
        return Task(delay, callback_f, *args, **kwds)

    def sendto(self, data, addr):
        pass
    


    
class _SocketMock(object):

    def sendto(self, data, addr):
        if len(data) > BUFFER_SIZE:
            return BUFFER_SIZE
        raise socket.error

    def recvfrom(self, buffer_size):
        raise socket.error
