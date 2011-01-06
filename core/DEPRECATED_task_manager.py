# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

'''
Task manager

'''
raise DeprecationWarning

import threading
import ptime as time

import logging

logger = logging.getLogger('dht')

class Task(object):
    
    '''Simple container for a task '''

    def __init__(self, delay, callback_f, *args, **kwds):
        '''
        Create a task instance. Here is when the call time is calculated.

        '''
        self.delay = delay
        self.callback_f = callback_f
        self.args = args
        self.kwds = kwds
        self.call_time = time.time() + self.delay
        self._cancelled = False

    @property
    def cancelled(self):
        return self._cancelled
    
    def fire_callback(self):
        """Fire a callback (if it hasn't been cancelled)."""
        tasks_to_schedule = []
        msgs_to_send = []
        import sys
        if not self._cancelled:
            try:
                tasks_to_schedule, msgs_to_send = self.callback_f(
                    *self.args, **self.kwds)
            except:
                '''
                import sys
                print >>sys.stderr, '\n\n>>>>>>>>>>>>>>>>', self.__dict__
                raise
                '''
            # This task cannot be used again
            self._cancelled = True
        '''
        Tasks may have arguments which reference to the objects which
        created the task. That is, they create a memory cycle. In order
        to break the memoery cycle, those arguments are deleted.
        '''
        del self.callback_f
        del self.args
        del self.kwds
        return tasks_to_schedule, msgs_to_send

    def cancel(self):
        """Cancel a task (callback won't be called when fired)"""
        self._cancelled = True
        

class TaskManager(object):

    """Manage tasks"""

    def __init__(self):
        self.tasks = {}
        self.next_task = None

    def add(self, task):
        """Add task to the TaskManager"""

        if not task.callback_f:
            #no callback, just ignore. The code that created this callback
            #doesn't really call anything back, it probably created the task
            #because some function required a task (e.g. timeout_task).
            return
        ms_delay = int(task.delay * 1000)
        # we need integers for the dictionary (floats are not hashable)
        self.tasks.setdefault(ms_delay, []).append(task)
        if self.next_task is None or task.call_time < self.next_task.call_time:
            self.next_task = task

#    def __iter__(self):
#        """Makes (along with next) this objcet iterable"""
#        return self

    def _get_next_task(self):
        """Return the task which should be fired next"""
        
        next_task = None
        for _, task_list in self.tasks.items():
            task = task_list[0]
            if next_task is None:
                next_task = task
            if task.call_time < next_task.call_time:
                next_task = task
        return next_task
                

    def consume_task(self):
        """
        Return the task which should be fire next and removes it from
        TaskManager 

        """
        current_time = time.time()
        if self.next_task is None:
            # no pending tasks
            return None #raise StopIteration
        if self.next_task.call_time > current_time:
            # there are pending tasks but it's too soon to fire them
            return None #raise StopIteration
        # self.next_task is ready to be fired
        task = self.next_task
        # delete  consummed task and get next one (if any)
        ms_delay = int(self.next_task.delay * 1000)
        del self.tasks[ms_delay][0]
        if not self.tasks[ms_delay]:
            # delete list when it's empty
            del self.tasks[ms_delay]
        self.next_task = self._get_next_task()
        #TODO2: make it yield
        return task
