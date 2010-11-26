# Copyright (C) 2009-2010 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import sys

import logging

import message
import identifier
import ptime as time

logger = logging.getLogger('dht')

TIMEOUT_DELAY = 2

class Query(object):

    def __init__(self, msg, dstnode, lookup_obj=None):
        self.tid = None
        self.query_ts = None
        self.msg = msg
        self.dstnode = dstnode
        self.lookup_obj = lookup_obj
        self.got_response = False
        self.got_error = False

    def on_response_received(self, response_msg):
        self.rtt = time.time() - self.query_ts
        if not self.dstnode.id:
            self.dstnode.id = response_msg.sender_id
        self.got_response = True

    def on_error_received(self, error_msg):
        self.rtt = time.time() - self.query_ts
        self.got_error = True
        
    def matching_tid(self, response_tid):
        return message.matching_tid(self.tid, response_tid)

    
class Querier(object):

    def __init__(self, my_id):
        self.my_id = my_id
        self._pending = {}
        self._timeouts = []
        self._tid = [0, 0]

    def _next_tid(self):
        #TODO: move to message?
        current_tid_str = ''.join([chr(c) for c in self._tid])
        self._tid[0] = (self._tid[0] + 1) % 256
        if self._tid[0] == 0:
            self._tid[1] = (self._tid[1] + 1) % 256
        return current_tid_str # raul: yield created trouble

    def register_queries(self, queries):
        assert len(queries)
        bencoded_msgs = []
        current_ts = time.time()
        timeout_ts = current_ts + TIMEOUT_DELAY
        for query in queries:
            logger.critical('%r' % (query))
            query.tid = self._next_tid()
            logger.debug('registering query to node: %r\n%r' % (query.dstnode,
                                                                query.msg))
            query.query_ts = current_ts
            self._timeouts.append((timeout_ts, query))
            # if node is not in the dictionary, it will create an empty list
            self._pending.setdefault(query.dstnode.addr, []).append(query)
            bencoded_msgs.append((query.msg.encode(query.tid),
                                  query.dstnode.addr))
        return timeout_ts, bencoded_msgs

    def on_response_received(self, response_msg, addr):
        # message already sanitized by IncomingMsg
        logger.debug('response received: %s' % repr(response_msg))
        related_query = self._find_related_query(addr, response_msg.tid)
        if related_query:
            # This response matches query. Notify query.
            related_query.on_response_received(response_msg)
        else:
            logger.warning('No query for this response\n%s\nsource: %s' % (
                    response_msg, addr))
        return related_query
            
    def on_error_received(self, error_msg, addr):
        logger.warning('Error message received:\n%s\nSource: %s',
                        `error_msg`,
                        `addr`)
        related_query = self._find_related_query(addr, error_msg.tid)
        if related_query:
            related_query.on_error_received(error_msg)
        return related_query

    def get_timeout_queries(self):
        current_ts = time.time()
        timeout_queries = []
        while self._timeouts:
            timeout_ts, query = self._timeouts[0]
            if current_ts < timeout_ts:
                break
            self._timeouts = self._timeouts[1:]
            addr_query_list = self._pending[query.dstnode.addr]
            assert query == addr_query_list.pop(0)
            if not addr_query_list:
                # The list is empty. Remove the whole list.
                del self._pending[query.dstnode.addr]
            if not query.got_response and not query.got_error:
                timeout_queries.append(query)
        return timeout_queries

    def _find_related_query(self, addr, tid):
        try:
            addr_query_list = self._pending[addr]
        except (KeyError):
            logger.warning('No pending queries for %s', addr)
            return # Ignore response
        for related_query in addr_query_list:
            if related_query.matching_tid(tid):
                logger.debug(
                    'response node: %s, related query: (%s), delay %f s.' % (
                        `addr`,
                        `related_query.msg.query`,
                        time.time() - related_query.query_ts))
                # Do not delete this query (the timeout will delete it)
                return related_query
