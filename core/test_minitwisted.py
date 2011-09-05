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
from testing_mocks import MockTimeoutSocket

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

MAIN_LOOP_DELAY = tc.TASK_INTERVAL * 10

class CrashError(Exception):
    'Used to test crashing callbacks'
    pass

class TestMinitwisted:

    def _main_loop(self):
        with self.lock:
            self.main_loop_call_counter += 1
        return time.time() + self.main_loop_delay, []

    def _main_loop_return_datagrams(self):
        return time.time() + self.main_loop_delay, [DATAGRAM1]

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
        raise CrashError, 'Crash testing'

    def setup(self):
        time.mock_mode()
        self.main_loop_call_counter = 0
        self.callback_values = []
        self.datagrams_received = []
        
        self.lock = threading.RLock()
        self.main_loop_delay = MAIN_LOOP_DELAY
        self.reactor = ThreadedReactor(self._main_loop,
                                       tc.CLIENT_PORT,
                                       self._on_datagram_received,
                                       task_interval=tc.TASK_INTERVAL)
        self.reactor.s = _SocketMock(tc.TASK_INTERVAL)
        self.s = self.reactor.s
        #self.reactor.start() >> instead of usint start(), we use run_one_step()

    def test_call_main_loop(self):
        eq_(self.main_loop_call_counter, 0)
        self.reactor.run_one_step()
        # main_loop is called right away
        eq_(self.main_loop_call_counter, 1)
        self.reactor.run_one_step()
        # no events
        eq_(self.main_loop_call_counter, 1)
        time.sleep(self.main_loop_delay)
        self.reactor.run_one_step()
        # main_loop is called again after 
        eq_(self.main_loop_call_counter, 2)
        
    def test_call_asap(self):
        eq_(self.callback_values, [])
        self.reactor.call_asap(self._callback, 0)
        eq_(self.callback_values, []) # stil nothing
        self.reactor.run_one_step()
        eq_(self.callback_values, [0]) #callback triggered
        for i in xrange(1, 5):
            self.reactor.call_asap(self._callback, i)
            self.reactor.run_one_step()
            eq_(self.callback_values, range(i + 1))
    
    def test_minitwisted_crashed(self):
        self.reactor.call_asap(self._crashing_callback)
        assert_raises(CrashError, self.reactor.run_one_step)

    def test_on_datagram_received_callback(self):
        eq_(self.datagrams_received, [])
        self.reactor.run_one_step()
        eq_(self.datagrams_received, [])
        datagram = Datagram(DATA1, tc.SERVER_ADDR)
        # This is equivalent to sending a datagram to reactor
        self.s.put_datagram_received(datagram)
        self.reactor.run_one_step()
        eq_(len(self.datagrams_received), 1)
        eq_(self.datagrams_received[0], datagram)

    def _test_block_flood(self):
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
        # TODO
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
        #self.reactor.stop() >> reactor is not really running
        time.normal_mode()


class _TestSend:

    
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
        raise CrashError, 'Crash testing'

    def setup(self):
        self.main_loop_call_counter = 0
        self.callback_values = []
        self.datagrams_received = []
        
        self.lock = threading.RLock()
        self.reactor = ThreadedReactor(self._main_loop,
                                       tc.CLIENT_PORT,
                                       self._on_datagram_received,
                                       task_interval=tc.TASK_INTERVAL)
        self.reactor.s = _SocketMock(tc.TASK_INTERVAL)
        self.s = self.reactor.s
        self.reactor.start()
        
    def _test_main_loop_send_data(self):
        time.sleep(tc.TASK_INTERVAL)
        eq_(self.s.get_datagrams_sent(), [DATAGRAM1])
        return
    
    def _test_call_asap_send_data(self):
        time.sleep(tc.TASK_INTERVAL)
        eq_(self.s.get_datagrams_sent(), [DATAGRAM1])
        self.reactor.call_asap(self._callback, 1)
        time.sleep(tc.TASK_INTERVAL*2)
        eq_(self.s.get_datagrams_sent(), [DATAGRAM1, DATAGRAM2])
        
    def _test_on_datagram_received_send_data(self): 
        time.sleep(tc.TASK_INTERVAL)
        eq_(self.s.get_datagrams_sent(), [DATAGRAM1])
        self.s.put_datagram_received(Datagram(DATA1, tc.SERVER_ADDR))
        time.sleep(tc.TASK_INTERVAL/2)
        eq_(self.s.get_datagrams_sent(), [DATAGRAM1, DATAGRAM3])
        
    def _test_capture(self):
        self.reactor.start_capture()
        ts1 = time.time()
        time.sleep(tc.TASK_INTERVAL)
        ts2 = time.time()
        self.s.put_datagram_received(Datagram(DATA1, tc.SERVER_ADDR))
        time.sleep(tc.TASK_INTERVAL/2)
        captured_msgs = self.reactor.stop_and_get_capture()

        #FIXME: sometimes 2, sometimes 3
        eq_(len(captured_msgs), 3)
        for msg in  captured_msgs:
            print msg
        assert ts1 < captured_msgs[0][0] < ts2
        eq_(captured_msgs[0][1], tc.SERVER_ADDR)
        eq_(captured_msgs[0][2], True) #outgoing
        eq_(captured_msgs[0][3], DATA1)
        assert captured_msgs[1][0] > ts2
        eq_(captured_msgs[1][1], DATAGRAM1.addr)
        eq_(captured_msgs[1][2], False) #incoming
        eq_(captured_msgs[1][3], DATAGRAM1.data)
#        assert captured_msgs[2][0] > captured_msgs[1][0]
#        eq_(captured_msgs[2][1], DATAGRAM3.addr)
#        eq_(captured_msgs[2][2], True) #outgoing
#        eq_(captured_msgs[2][3], DATAGRAM3.data)
        
    def teardown(self):
        self.reactor.stop()

        
class _TestSocketError:

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
        self.reactor.s = _SocketMock(tc.TASK_INTERVAL)
        self.s = self.reactor.s
        self.reactor.start()
        self.reactor.call_asap(self._very_long_callback)
        time.sleep(tc.TASK_INTERVAL*2)
        assert_raises(Exception, self.reactor.stop)
    




    
        
class _TestSocketErrors:

    def _main_loop(self): 
        return time.time() + tc.TASK_INTERVAL*10000, []
   
    def _main_loop_send(self):
        self.main_loop_send_called = True
        logger.critical('main loop returns datagram!!!!')
        return time.time() + tc.TASK_INTERVAL*10000, [DATAGRAM1]
   
    def _callback(self, *args, **kwargs):
        self.callback_fired = True

    def _on_datagram_received(self, datagram):
        return time.time() + 100, []

    def setup(self):
        self.main_loop_send_called = False
        self.callback_fired = False
        self.r = ThreadedReactor(self._main_loop_send, tc.CLIENT_PORT,
                                 self._on_datagram_received)
        self.r.s = _SocketErrorMock()
        #self.r.listen_udp(tc.CLIENT_PORT, lambda x,y:None)

    def test_sendto(self):
        logger.critical('TESTING: IGNORE CRITICAL MESSAGE')
        assert not self.main_loop_send_called
        self.r.start()
        while not self.r.running:
            time.sleep(tc.TASK_INTERVAL)
        while not self.main_loop_send_called:
            time.sleep(tc.TASK_INTERVAL)
        assert self.r.s.error_raised
        assert self.r.running # reactor doesn't crashed

    def _test_recvfrom(self):
        #self.r.start()
        r2 = ThreadedReactor(self._main_loop, tc.CLIENT_PORT,
                             self._on_datagram_received,
                             task_interval=tc.TASK_INTERVAL)
        r2.s = _SocketErrorMock()
        assert not r2.running
        r2.start()
        assert r2.running
        logger.critical('TESTING: IGNORE CRITICAL MESSAGE')
        # self.r will call recvfrom (which raises socket.error)
        while not r2.s.error_raised:
            time.sleep(tc.TASK_INTERVAL)
        assert r2.running # the error is ignored
        ok_(not self.callback_fired)
        r2.stop()

    def _test_sendto_too_large_data_string(self):
        logger.critical('TESTING: IGNORE CRITICAL MESSAGE')
        self.r.sendto('z'*12345, tc.NO_ADDR)

    def tear_down(self):
        selr.r.stop()
        pass

class _SocketMock(object):

    def __init__(self, timeout_delay):
        self.timeout_delay = timeout_delay
        self.lock = threading.RLock()
        self.datagrams_sent = []
        self.datagrams_received = []
        self.num_send_errors = 0
        self.num_recvfrom_errors = 0
        self.num_recvfrom_timeouts = 0

        self.raise_error_on_send = False
        self.raise_error_on_recvfrom = False
        self.raise_timeout = False
        
    def sendto(self, data, addr):
        if self.raise_error_on_send:
            self.raise_error_on_send = False
            self.num_send_errors += 1
            raise socket.error
        with self.lock:
            self.datagrams_sent.append(Datagram(data, addr))
        return min(20, len(data))
    
    def recvfrom(self, buffer_size):
        datagram_received = None
        if self.raise_error_on_recvfrom:
            self.raise_error_on_recvfrom = False
            self.num_recvfrom_errors += 1
            raise socket.error
        if self.datagrams_received:
            datagram_received = self.datagrams_received.pop(0)
        if datagram_received:
            return (datagram_received.data, datagram_received.addr)
        # nothing to do, raise timeout
        self.raise_timeout_on_next_recvfrom = False
        self.num_recvfrom_timeouts += 1
        raise socket.timeout
        
    def put_datagram_received(self, datagram, delay=0):
        with self.lock:
            self.datagrams_received.append(datagram)

    def get_datagrams_sent(self):
        with self.lock:
            datagrams_sent = [d for d in self.datagrams_sent]
        return datagrams_sent

    def raise_error_on_next_recvfrom(self):
        self.raise_error_on_recvfrom = True

    def raise_timeout_on_next_recvfrom(self):
        self.raise_timeout = True

    def raise_error_on_next_send(self):
        self.raise_error_on_send = True
    
class _SocketErrorMock(object):

    def __init__(self):
        self.error_raised = False
    
    def sendto(self, data, addr):
        self.error_raised = True
        raise socket.error

    def recvfrom(self, buffer_size):
        self.error_raised = True
        raise socket.error

        
