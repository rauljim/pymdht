
import core.message as message
from core.node import Node
import core.ptime as time
import pickle

STATUS_PINGED = 'PINGED'
STATUS_OK = 'OK'
STATUS_FAIL = 'FAIL'

NUM_REPETITIONS = 5


class ExperimentalManager:
    def __init__(self, my_id):
        self.my_id = my_id
        self._send_query = True
        self.num_responses = 0
    def on_query_received(self, msg):
        find_msgs = []
        if self._send_query:
            # We only want to extract from ONE node
            self._send_query = False
            print '\nExtractRoutingTable got query (%s) from  node  %r =' % (
                            msg.query ,  msg.src_node)
            print '===================='
            exp_obj = ExpObj()
            target = msg.src_node.id.generate_close_id(
                                            exp_obj.next_log_dist())
            find_msgs.append(message.OutgoingFindNodeQuery(msg.src_node,
                                                           self.my_id,
                                                           target, None,
                                                           exp_obj))
        return find_msgs
    def on_response_received(self, msg, related_query):
        ping_msgs = []
        exp_obj = related_query.experimental_obj
        if not exp_obj:
            # this is not a extracting related response, nothing to do here
            return
        if related_query.query == message.PING:
            print 'ping OK'
            #TODO
            return
        #print exp_obj.num_repetitions, 'response', msg.all_nodes
        for node_ in msg.all_nodes:
            if node_.id in exp_obj.all_ids:
                # repetition
                exp_obj.num_repetitions += 1
            else:
                ping_msgs.append(message.OutgoingPingQuery(msg.src_node,
                                                           self.my_id,
                                                           exp_obj))
        exp_obj.save_bucket(msg.all_nodes)
        if exp_obj.num_repetitions > NUM_REPETITIONS:
            exp_obj.print_nodes()
            #END OF EXTRACTION
            return
        find_msgs = []
        target = msg.src_node.id.generate_close_id(exp_obj.next_log_dist())
        find_msgs.append(message.OutgoingFindNodeQuery(msg.src_node,
                                                        self.my_id,target,
                                                       None, exp_obj))
        print 'sending %d fn and %d pings' % (len(find_msgs), len(ping_msgs))
        msgs_to_send = find_msgs + ping_msgs # send pings and continue extracting
        return msgs_to_send
    def on_timeout(self, related_query):
        if related_query.experimental_obj:
            print 'Timeout', related_query.query

    def on_error(self, related_query):
        # this will never be called by controller!!!
        raise Exception

    def on_stop(self):
        pass
class ExpObj:
    def __init__(self):
        self.current_log_dist = 160
        self.num_repetitions = 0
        self.nodes = []
        self.all_ids = set()
        self._queue_bucket = []
    def next_log_dist(self):
        self.current_log_dist -= 1
        return self.current_log_dist
    def save_bucket(self, nodes):
        self.nodes.append((self.current_log_dist, nodes))
        #print 'Save-bucket:'
        for node_ in nodes:
            self.all_ids.add(node_.id)
    def print_nodes(self):
         for logdist, nodes in self.nodes:
            print 'Log Distance = ', logdist
            for node_ in nodes:
                print node_