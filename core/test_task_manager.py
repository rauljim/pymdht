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
from testing_mocks import MockTimeoutSocket

logging_conf.testing_setup(__name__)
logger = logging.getLogger('dht')


import task_manager
from task_manager import Task, TaskManager#, ThreadedReactor
#from minitwisted import ThreadedReactorSocketError, _SocketMock


ADDRS= (tc.CLIENT_ADDR, tc.SERVER_ADDR)
DATA = 'testing...'


class _TestTaskManager:
    
    def callback_f(self, callback_id):
        tasks_to_schedule = []
        msgs_to_send = []
        self.callback_order.append(callback_id)
        return tasks_to_schedule, msgs_to_send
        
    def setup(self):
        time.mock_mode()
        # Order in which callbacks have been fired
        self.callback_order = []
        self.task_m = TaskManager()

    def test_simple(self):
        for i in xrange(5):
            task = Task(1, self.callback_f, i)
            self.task_m.add(task)
            print task.callback_f, task.call_time
        ok_(not self.task_m.consume_task())

        time.sleep(1)

        for i in xrange(5):
            task = self.task_m.consume_task()
            task.fire_callback() 
        ok_(not self.task_m.consume_task())
        ok_(self.callback_order, range(5))

    def test_cancel(self):
        tasks = [Task(1, self.callback_f, i) for i in xrange(10)]
        task_to_be_canceled = tasks[5]
        for task in tasks:
            self.task_m.add(task)
        eq_(self.task_m.consume_task(), None)
        eq_(self.callback_order, [])
        ok_(not task_to_be_canceled.cancelled)
        task_to_be_canceled.cancel()
        ok_(task_to_be_canceled.cancelled)
        
        time.sleep(1)

        while True:
            task = self.task_m.consume_task()
            if task is None:
                break
            task.fire_callback()
        eq_(self.callback_order, [0, 1 ,2 ,3 ,4,   6, 7, 8, 9])

    def test_different_delay(self):
#         NOTICE: this test might fail if your configuration
#         (interpreter/processor) is too slow
        
        task_delays = (1, 1, 1, .5, 1, 1, 2, 1, 1, 1,
                       1, 1.5, 1, 1, 1, 1, .3)
                       
        expected_list = ([],
                         ['a', 16, 3, 'b'], #9 is cancelled
                         ['a', 0, 1, 2, 4, 5, 7, 8, 10, 12, 13, 15, 'c', 'b'],
                         ['a', 11, 'c', 'b'],
                         ['a', 6, 'c', 'b'],
            )
        tasks = [Task(delay, self.callback_f, i) \
                 for i, delay in enumerate(task_delays)]
        for task in tasks:
            self.task_m.add(task)

        for i, expected in enumerate(expected_list):
            while True:
                task = self.task_m.consume_task()
                if task is None:
                    break
                task.fire_callback()
            logger.debug('#: %d, result: %s, expected: %s' % (i,
                                              self.callback_order, expected))
            assert self.callback_order == expected
            self.callback_order = []
            self.task_m.add(Task(0, self.callback_f, 'a'))
            self.task_m.add(Task(.5, self.callback_f, 'b'))
            self.task_m.add(Task(1, self.callback_f, 'c'))
            time.sleep(.5)
            tasks[9].cancel() # too late (already fired) 
            tasks[14].cancel() # should be cancelled

    def _callback1(self, arg1, arg2):
        if arg1 == 1 and arg2 == 2:
            self.callback_order.append(1)
    def _callback2(self, arg1, arg2):
        if arg1 == 1 and arg2 == 2:
            self.callback_order.append(2)
    
    def _DEPRECATED_test_callback_list(self):
        self.task_m.add(Task(tc.TASK_INTERVAL/2,
                              [self._callback1, self._callback2],
                              1, 2))
        ok_(self.task_m.consume_task() is None)
        eq_(self.callback_order, [])
        time.sleep(tc.TASK_INTERVAL)
        self.task_m.consume_task().fire_callback()
        eq_(self.callback_order, [1,2])

    def teardown(self):
        time.normal_mode()
