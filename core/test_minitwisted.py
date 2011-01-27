# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

from __future__ import with_statement

import logging
import sys
import threading
import socket

from nose.tools import eq_, ok_, assert_raises

import logging_conf
import ptime as time
import test_const as tc
from message import Datagram
from testing_mocks import MockTimeoutSocket#, MockTime

import minitwisted
from minitwisted import ThreadedReactor

logging_conf.testing_setup(__name__)
logger = logging.getLogger('dht')

DATA1 = 'testing...1'
DATA2 = 'testing...2'
DATA3 = 'testing...3...................'
DATAGRAM1 = Datagram(DATA1, tc.SERVER_ADDR)
DATAGRAM2 = Datagram(DATA2, tc.SERVER2_ADDR)
DATAGRAM3 = Datagram(DATA3, tc.SERVER2_ADDR)




class TestMinitwisted:

    def _main_loop(self):
        with self.lock:
            self.main_loop_call_counter += 1
        return time.time() + tc.TASK_INTERVAL*10, []

    def _main_loop_return_datagrams(self):
        return time.time() + tc.TASK_INTERVAL*10, [DATAGRAM1]

    def _callback(self, value):
        with self.lock:
            self.callback_values.append(value)
        return time.time() + 100, []

    def _very_long_callback(self, value):
        time.sleep(tc.TASK_INTERVAL*11)

    def _on_datagram_received(self, datagram):
        print 'on_datagram', datagram, datagram.data, datagram.addr
        with self.lock:
            self.datagrams_received.append(datagram)
        return time.time() + 100, []

    def _crashing_callback(self):
        raise Exception, 'Crash testing'

    def setup(self):
        self.main_loop_call_counter = 0
        self.callback_values = []
        self.datagrams_received = []
        
        self.lock = threading.RLock()
        self.reactor = ThreadedReactor(self._main_loop,
                                       tc.CLIENT_PORT,
                                       self._on_datagram_received,
                                       task_interval=tc.TASK_INTERVAL)
        self.reactor.s = _SocketMock()
        self.s = self.reactor.s
        self.reactor.start()

    def test_call_main_loop(self):
        time.sleep(tc.TASK_INTERVAL)
        # main_loop is called right away
        with self.lock:
            eq_(self.main_loop_call_counter, 1)
        time.sleep(.1 + tc.TASK_INTERVAL)
        with self.lock:
            #FIXME: this crashes when recompiling
            eq_(self.main_loop_call_counter, 2)
        
    def test_call_asap(self):
        with self.lock:
            eq_(self.callback_values, [])
        self.reactor.call_asap(self._callback, 0)
        time.sleep(tc.TASK_INTERVAL*2)
        with self.lock:
            eq_(self.callback_values, [0])
    
        for i in xrange(1, 5):
            self.reactor.call_asap(self._callback, i)
            time.sleep(tc.TASK_INTERVAL*3)
            with self.lock:
                eq_(self.callback_values, range(i + 1))
    
    def test_minitwisted_crashed(self):
        self.reactor.call_asap(self._crashing_callback)
        time.sleep(tc.TASK_INTERVAL*3)
        # from now on, the minitwisted thread is dead
        ok_(not self.reactor.running)

    def test_on_datagram_received_callback(self):
        # This is equivalent to sending a datagram to reactor
        self.s.put_datagram_received(Datagram(DATA1, tc.SERVER_ADDR))
        datagram = Datagram(DATA1, tc.SERVER_ADDR)
        print '--------------', datagram, datagram.data, datagram.addr
        time.sleep(tc.TASK_INTERVAL*1)
        with self.lock:
            datagram = self.datagrams_received.pop(0)
            print 'popped>>>>>>>>>>>>>>>', datagram
            eq_(datagram.data, DATA1)
            eq_(datagram.addr, tc.SERVER_ADDR)

    def test_block_flood(self):
        from floodbarrier import MAX_PACKETS_PER_PERIOD as FLOOD_LIMIT
        for _ in xrange(FLOOD_LIMIT):
            self.s.put_datagram_received(Datagram(DATA1, tc.SERVER_ADDR))
        time.sleep(tc.TASK_INTERVAL*5)
        with self.lock:
            eq_(len(self.datagrams_received), FLOOD_LIMIT)
        for _ in xrange(10):
            self.s.put_datagram_received(Datagram(DATA1, tc.SERVER_ADDR))
            time.sleep(tc.TASK_INTERVAL*3)
            with self.lock:
                eq_(len(self.datagrams_received), FLOOD_LIMIT)
                logger.warning(
                    "TESTING LOGS ** IGNORE EXPECTED WARNING **")

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
        self.server_r.sendto(DATA, tc.CLIENT_PORT)
        time.sleep(.02) # wait for network interruption
        with self.lock:
            logger.debug('callback_order: %s' % self.callback_order)
            assert self.callback_order == []
            logger.debug('callback_order: %s' % self.callback_order)
            datagram = self.datagrams_received.pop(0)
            eq_(datagram.data, DATA)
            eq_(datagram.addr, tc.SERVER_ADDR)
            task2.cancel() #inside critical region??
        time.sleep(.1) # wait for task 0 (task 2 should be cancelled)
        with self.lock:
            assert self.callback_order == [0]
            assert not self.datagrams_received

    def teardown(self):
        self.reactor.stop()


class TestSend:

    
    def _main_loop(self):
        return time.time() + 100, [DATAGRAM1]

    def _callback(self, value):
        with self.lock:
            self.callback_values.append(value)
        return time.time() + 100, [DATAGRAM2]

    def _on_datagram_received(self, datagram):
        with self.lock:
            self.datagrams_received.append(datagram)
        return time.time() + 100, [DATAGRAM3]

    def _crashing_callback(self):
        raise Exception, 'Crash testing'

    def setup(self):
        self.main_loop_call_counter = 0
        self.callback_values = []
        self.datagrams_received = []
        
        self.lock = threading.RLock()
        self.reactor = ThreadedReactor(self._main_loop,
                                       tc.CLIENT_PORT,
                                       self._on_datagram_received,
                                       task_interval=tc.TASK_INTERVAL)
        self.reactor.s = _SocketMock()
        self.s = self.reactor.s
        self.reactor.start()
        
    def test_main_loop_send_data(self):
        time.sleep(tc.TASK_INTERVAL)
        eq_(self.s.get_datagrams_sent(), [DATAGRAM1])
        return
    
    def test_call_asap_send_data(self):
        time.sleep(tc.TASK_INTERVAL)
        eq_(self.s.get_datagrams_sent(), [DATAGRAM1])
        self.reactor.call_asap(self._callback, 1)
        time.sleep(tc.TASK_INTERVAL*2)
        eq_(self.s.get_datagrams_sent(), [DATAGRAM1, DATAGRAM2])
        
    def test_on_datagram_received_send_data(self): 
        time.sleep(tc.TASK_INTERVAL)
        eq_(self.s.get_datagrams_sent(), [DATAGRAM1])
        self.s.put_datagram_received(Datagram(DATA1, tc.SERVER_ADDR))
        time.sleep(tc.TASK_INTERVAL/2)
        eq_(self.s.get_datagrams_sent(), [DATAGRAM1, DATAGRAM3])
        
    def teardown(self):
        self.reactor.stop()

        
class TestSocketError:

    def _main_loop(self):
        return time.time() + tc.TASK_INTERVAL*10000, [DATAGRAM1]

    def _on_datagram_received(self):
        return
    
    def setup(self):
        self.main_loop_call_counter = 0
        self.callback_values = []
        self.datagrams_received = []
        
        self.lock = threading.RLock()
        self.reactor = ThreadedReactor(self._main_loop,
                                       tc.CLIENT_PORT,
                                       self._on_datagram_received,
                                       task_interval=tc.TASK_INTERVAL)
        self.reactor.s = _SocketErrorMock()
        self.reactor.start()

    def test_sendto_socket_error(self): 
        time.sleep(tc.TASK_INTERVAL/5)

    def teardown(self):
        self.reactor.stop()




class _TestError:

    def _main_loop(self):
        return time.time() + 100, []

    def _very_long_callback(self):
        time.sleep(tc.TASK_INTERVAL*15)
        return time.time() + 100, []

    def _on_datagram_received(self, datagram):
        return time.time() + 100, []

    def _crashing_callback(self):
        raise Exception, 'Crash testing'

    def test_failed_join(self):
        self.lock = threading.RLock()
        self.reactor = ThreadedReactor(self._main_loop,
                                       tc.CLIENT_PORT,
                                       self._on_datagram_received,
                                       task_interval=tc.TASK_INTERVAL)
        self.reactor.s = _SocketMock()
        self.s = self.reactor.s
        self.reactor.start()
        self.reactor.call_asap(self._very_long_callback)
        time.sleep(tc.TASK_INTERVAL*2)
        assert_raises(Exception, self.reactor.stop)
    




    
        
class _TestSocketErrors:

    def _callback(self, *args, **kwargs):
        self.callback_fired = True
    
    def setup(self):
        self.callback_fired = False
        self.r = ThreadedReactorSocketError()
        self.r.listen_udp(tc.CLIENT_PORT, lambda x,y:None)

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
            

class _SocketMock(object):

    def __init__(self):
        self.lock = threading.RLock()
        self.datagrams_sent = []
        self.datagrams_received = []
        
    def sendto(self, data, addr):
        with self.lock:
            self.datagrams_sent.append(Datagram(data, addr))
        return min(20, len(data))
    
    def recvfrom(self, buffer_size):
        datagram_received = None
        for i in xrange(9):
            time.sleep(tc.TASK_INTERVAL/10)
            with self.lock:
                if self.datagrams_received:
                    datagram_received = self.datagrams_received.pop(0)
            if datagram_received:
                return (datagram_received.data, datagram_received.addr)
        raise socket.timeout

    def put_datagram_received(self, datagram):
        with self.lock:
            self.datagrams_received.append(datagram)

    def get_datagrams_sent(self):
        with self.lock:
            datagrams_sent = [d for d in self.datagrams_sent]
        return datagrams_sent
        
class _SocketErrorMock(object):

    def sendto(self, data, addr):
        raise socket.error

    def recvfrom(self, buffer_size):
        raise socket.error

        
