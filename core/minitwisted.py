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
    def __init__(self, task_interval=0.1,
                 floodbarrier_active=True):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        
        self.running = False
        self._lock = threading.RLock()

        self.last_task_run_ts = 0
        self.task_interval = task_interval
        self.floodbarrier_active = floodbarrier_active
        self.tasks = TaskManager()
        if self.floodbarrier_active:
            self.floodbarrier = FloodBarrier()

    #@profile
    def run(self):
        self.running = True
        try:
            while self.running:
                self._protected_run()
        except:
            self.running = False
            logger.critical('MINITWISTED CRASHED')
            logger.exception('MINITWISTED CRASHED')
        print 'Reactor stopped!'
        logger.debug('Reactor stopped')

    def _protected_run(self):
        """Main loop activated by calling self.start()"""
        
        tasks_to_schedule = []
        msgs_to_send = []
        # Perfom scheduled tasks
        if time.time() - self.last_task_run_ts > self.task_interval:
            #with self._lock:
            self._lock.acquire()
            try:
                while True:
                    task = self.tasks.consume_task()
                    if task is None:
                        break
                    (tasks_to_schedule,
                     msgs_to_send) = task.fire_callback()
                    self.last_task_run_ts = time.time()
            finally:
                self._lock.release()
        for task in tasks_to_schedule:
            self.tasks.add(task)
        for msg, addr in msgs_to_send:
            logger.debug('TASK Sending to %r\n%r' % (addr, msg))
            self.sendto(msg, addr)
        # Get data from the network
        tasks_to_schedule = []
        msgs_to_send = []
        try:
            data, addr = self.s.recvfrom(BUFFER_SIZE)
        # except (AttributeError):
        #     logger.warning('udp_listen has not been called')
        #     time.sleep(self.task_interval)
        #     #TODO2: try using Event and wait
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
            else:
                (tasks_to_schedule,
                 msgs_to_send) = self.datagram_received_f(
                    data, addr)
        for task in tasks_to_schedule:
            self.tasks.add(task)
        for msg, addr in msgs_to_send:
            self.sendto(msg, addr)
            
    def stop(self):
        """Stop the thread. It cannot be resumed afterwards"""
        #with self._lock:
        self._lock.acquire()
        try:
            self.running = False
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
        
    def call_later(self, delay, callback_f, *args, **kwds):
        """Call the given callback with given arguments in the future (delay
        seconds).

        """
        #with self._lock:
        self._lock.acquire()
        try:
            task = Task(delay, callback_f, *args, **kwds)
            self.tasks.add(task)
        finally:
            self._lock.release()
        return task
            
    def call_asap(self, callback_f, *args, **kwds):
        """Same as call_later with delay 0 seconds. That is, call as soon as
        possible""" 
        return self.call_later(0, callback_f, *args, **kwds)
        
        
    def sendto(self, data, addr):
        """Send data to addr using the UDP port used by listen_udp."""
        #with self._lock:
        self._lock.acquire()
        try:
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
        finally:
            self._lock.release()


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
