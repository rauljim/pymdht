# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

from __future__ import with_statement
import sys
import threading
import ptime as time

import logging, logging_conf

from nose.tools import eq_, ok_, assert_raises

import test_const as tc
from testing_mocks import MockTime, MockTimeoutSocket

logging_conf.testing_setup(__name__)
logger = logging.getLogger('dht')


import minitwisted
from minitwisted import Task, TaskManager, ThreadedReactor
from minitwisted import ThreadedReactorSocketError, _SocketMock


ADDRS= (tc.CLIENT_ADDR, tc.SERVER_ADDR)
DATA = 'testing...'

        
class TestMinitwisted:

    def _main_loop(self):
        pass
    
    def setup(self):
        global time
        #TODO: mock time and socket
        #time = minitwisted.time = MockTime()
        #minitwisted.socket = MockSocket()
        
        self.lock = threading.Lock()
        self.datagrams_received = []
        self.callback_order = []
        self.client_r = ThreadedReactor(self._main_loop,
                                        task_interval=tc.TASK_INTERVAL)
        self.server_r = ThreadedReactor(self._main_loop,
                                        task_interval=tc.TASK_INTERVAL)
        self.client_s = self.client_r.listen_udp(tc.CLIENT_ADDR[1],
                                                 self.on_datagram_received)
        self.server_s = self.server_r.listen_udp(tc.SERVER_ADDR[1],
                                                 self.on_datagram_received)
        self.client_r.start()
        self.server_r.start()

    def test_listen_upd(self):
        r = ThreadedReactor()
#        assert_raises(Exception, r.start)
        logger.warning(''.join(
            ('TESTING LOGS ** IGNORE EXPECTED WARNING ** ',
             '(udp_listen has not been called)')))
        assert_raises(AttributeError, r.sendto,
                      DATA, tc.SERVER_ADDR)
        r.stop()
        return
    ##################
        while 1: #waiting for data
            with self.lock:
                if self.datagrams_received:
                    break
            time.sleep(tc.TASK_INTERVAL)
        with self.lock:
            first_datagram = self.datagrams_received.pop(0)
            logger.debug('first_datagram: %s, %s' % (
                    first_datagram,
                    (DATA, tc.CLIENT_ADDR)))
            assert first_datagram, (DATA, tc.CLIENT_ADDR)
        r.stop()
            
    def _test_network_callback(self):
        self.client_r.sendto(DATA, tc.SERVER_ADDR)
        time.sleep(tc.TASK_INTERVAL)
        with self.lock:
            first_datagram = self.datagrams_received.pop(0)
            logger.debug('first_datagram: %s, %s' % (
                    first_datagram,
                    (DATA, tc.CLIENT_ADDR)))
            assert first_datagram, (DATA, tc.CLIENT_ADDR)

    def _test_block_flood(self):
        from floodbarrier import MAX_PACKETS_PER_PERIOD as FLOOD_LIMIT

        for _ in xrange(FLOOD_LIMIT):
            self.client_r.sendto(DATA, tc.SERVER_ADDR)
        for _ in xrange(10):
            self.client_r.sendto(DATA, tc.SERVER_ADDR)
            logger.warning(
                "TESTING LOGS ** IGNORE EXPECTED WARNING **")
            time.sleep(tc.TASK_INTERVAL)
        return
######################################
        with self.lock:
            logger.debug('datagram processed: %d/%d' % (
                              len(self.datagrams_received),
                              FLOOD_LIMIT))
            print len(self.datagrams_received)
            assert len(self.datagrams_received) <= FLOOD_LIMIT

    def _test_call_later(self):
        self.client_r.call_later(.13, self.callback_f, 1)
        self.client_r.call_later(.11, self.callback_f, 2)
        self.client_r.call_later(.01, self.callback_f, 3)
        task4 = self.client_r.call_later(.01, self.callback_f, 4)
        task4.cancel()
        time.sleep(.03)
        with self.lock:
            logger.debug('callback_order: %s' % self.callback_order)
            eq_(self.callback_order, [3])
            self.callback_order = []
        self.client_r.call_asap(self.callback_f, 5)
        time.sleep(.03)
        with self.lock:
            logger.debug('callback_order: %s' % self.callback_order)
            eq_(self.callback_order, [5])
            self.callback_order = []
        task6 = self.client_r.call_later(.03, self.callback_f, 6)
        task6.cancel()
        time.sleep(.1)
        with self.lock:
            logger.debug('callback_order: %s' % self.callback_order)
            eq_(self.callback_order, [2, 1])

    def _test_network_and_delayed(self):
        self.client_r.call_later(.2, self.callback_f, 0)
        self.client_r.call_asap(self.callback_f, 1)
        task2 = self.client_r.call_later(.2, self.callback_f, 2)
        with self.lock:
            eq_(self.callback_order, [])
        time.sleep(.1)

        with self.lock:
            logger.debug('callback_order: %s' % self.callback_order)
            assert self.callback_order == [1]
            self.callback_order = []
            assert not self.datagrams_received
        self.server_r.sendto(DATA, tc.CLIENT_ADDR)
        time.sleep(.02) # wait for network interruption
        with self.lock:
            logger.debug('callback_order: %s' % self.callback_order)
            assert self.callback_order == []
            logger.debug('callback_order: %s' % self.callback_order)
            assert self.datagrams_received.pop(0) == (DATA, tc.SERVER_ADDR)
            task2.cancel() #inside critical region??
        time.sleep(.1) # wait for task 0 (task 2 should be cancelled)
        with self.lock:
            assert self.callback_order == [0]
            assert not self.datagrams_received

    def _test_sendto_socket_error(self): 
        logger.critical('TESTING: IGNORE CRITICAL MESSAGE')
        self.client_r.sendto('z', (tc.NO_ADDR[0], 0))

    def teardown(self):
        self.client_r.stop()
        self.server_r.stop()

    def on_datagram_received(self, data, addr):
        tasks_to_schedule = []
        msgs_to_send = []
        with self.lock:
            self.datagrams_received.append((data, addr))
        return tasks_to_schedule, msgs_to_send

    def callback_f(self, callback_id):
        tasks_to_schedule = []
        msgs_to_send = []
        with self.lock:
            self.callback_order.append(callback_id)
        return tasks_to_schedule, msgs_to_send


class _TestSocketErrors:

    def _callback(self, *args, **kwargs):
        self.callback_fired = True
    
    def setup(self):
        self.callback_fired = False
        self.r = ThreadedReactorSocketError()
        self.r.listen_udp(tc.CLIENT_ADDR[1], lambda x,y:None)

    def test_sendto(self):
        logger.critical('TESTING: IGNORE CRITICAL MESSAGE')
        self.r.sendto('z', tc.NO_ADDR)

    def test_recvfrom(self):
        self.r.start()
        r2 = ThreadedReactor()
        r2.listen_udp(tc.SERVER_ADDR[1], lambda x,y:None)
        logger.critical('TESTING: IGNORE CRITICAL MESSAGE')
        r2.sendto('z', tc.CLIENT_ADDR)
        # self.r will call recvfrom (which raises socket.error)
        time.sleep(tc.TASK_INTERVAL)
        ok_(not self.callback_fired)
        self.r.stop()

    def test_sendto_too_large_data_string(self):
        logger.critical('TESTING: IGNORE CRITICAL MESSAGE')
        self.r.sendto('z'*12345, tc.NO_ADDR)
            


        
class _TestMockThreadedReactor:

    def setup(self):
        pass

    def _callback(self, *args):
        pass

    def test_mock_threaded_reactor(self):
        '''
        Just making sure that the interface is the same

        '''
        r = ThreadedReactor(task_interval=.1)
        rm = ThreadedReactorMock(task_interval=.1)

        r.listen_udp(tc.CLIENT_ADDR[1], lambda x,y:None)
        rm.listen_udp(tc.CLIENT_ADDR[1], lambda x,y:None)

        r.start()
        rm.start()

        r.sendto(DATA, tc.CLIENT_ADDR)
        rm.sendto(DATA, tc.CLIENT_ADDR)
        
        r.call_later(.1, self._callback)
        rm.call_later(.1, self._callback)
#        time.sleep(.002)
        r.stop()
        rm.stop()
