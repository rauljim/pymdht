
import core.message as message
from core.node import Node
import core.ptime as time


STATUS_PINGED = 'PINGED'
STATUS_OK = 'OK'
STATUS_FAIL = 'FAIL'
STATUS_ERROR = 'ERROR'

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
            print 'Got query (%s) from  Node  %r ' % (
                            msg.query ,  msg.src_node)
            print '=============================================='
            exp_obj = ExpObj()
            target = msg.src_node.id.generate_close_id(
                                            exp_obj.next_log_dist())
            print 'Target %r'  % (target)
            print 'Sending first find_node'
            find_msgs.append(message.OutgoingFindNodeQuery(msg.src_node,
                                                           self.my_id,
                                                           target, None,
                                                           exp_obj))
            exp_obj.num_pending_queries += 1
            return find_msgs
        
    def on_response_received(self, msg, related_query):
        find_msgs = []
        ping_msgs = []
        exp_obj = related_query.experimental_obj
        if not exp_obj:
            # this is not a extracting related response, nothing to do here
            return
        print 'got response', related_query.query
        if related_query.query == message.PING:
            exp_obj.reg_ping_result(msg.src_node, STATUS_OK)
        elif related_query.query == message.FIND_NODE:
            #print exp_obj.num_repetitions, 'response', msg.all_nodes
            print 'got %d all_nodes' % len(msg.all_nodes)
            for node_ in msg.all_nodes:
                if node_.id in exp_obj.all_ids:
                    # repetition
                    exp_obj.num_repetitions += 1
                    print '>>repetition', exp_obj.num_repetitions
                else:
                    #time.sleep(0.01)
                    ping_msgs.append(message.OutgoingPingQuery(node_,
                                                               self.my_id,
                                                               exp_obj))
            log_distance_bucket = related_query.target.log_distance(related_query.dst_node.id) 
            exp_obj.save_bucket(log_distance_bucket, msg.all_nodes)
            if exp_obj.num_repetitions < NUM_REPETITIONS:
                target = msg.src_node.id.generate_close_id(exp_obj.next_log_dist())
                print 'target:', msg.src_node.id.log_distance(target) 
                find_msgs.append(message.OutgoingFindNodeQuery(msg.src_node,
                                                               self.my_id,
                                                               target,
                                                               None,
                                                               exp_obj))
            
            print 'Sending %d find and %d pings' % (len(find_msgs),
                                                    len(ping_msgs))            
        exp_obj.num_pending_queries -= 1
            #END OF EXTRACTION
        msgs_to_send = find_msgs + ping_msgs # send pings and continue extracting
        exp_obj.num_pending_queries += len(msgs_to_send)
        if not exp_obj.num_pending_queries:     
            exp_obj.print_nodes()
        return msgs_to_send
    
    def on_timeout(self, related_query):
        exp_obj = related_query.experimental_obj 
        if  exp_obj:
            print 'Timeout', related_query.query
            if related_query.query == message.PING:
                exp_obj.reg_ping_result(
                                        related_query.dst_node, 
                                        STATUS_FAIL)
            exp_obj.num_pending_queries -= 1
            if not exp_obj.num_pending_queries:     
                exp_obj.print_nodes()

    def on_error_received(self, msg, related_query):
        exp_obj = related_query.experimental_obj
        if exp_obj:
            print 'got ERROR', related_query.query
            if related_query.query == message.PING:
                exp_obj.reg_ping_result(
                                        related_query.dst_node, 
                                        STATUS_ERROR)
            exp_obj.num_pending_queries -= 1
            if not exp_obj.num_pending_queries:     
                exp_obj.print_nodes()

    def on_stop(self):
        pass
    
    def _print_staus(self):
        for ip, status in self.pinged_ips.iteritems():
            print('%s\t %s\n' % (ip, status))
        pass

class ExpObj:
    def __init__(self):
        self.current_log_dist = 160
        self.num_repetitions = 0
        self.nodes = []
        self.all_ids = set()
        self.status = {}
        self.num_pending_queries = 0
        
    def next_log_dist(self):
        self.current_log_dist -= 1
        return self.current_log_dist
    
    def save_bucket(self, log_distance_bucket, nodes):
        self.nodes.append((log_distance_bucket, nodes))
        #print 'Save-bucket:'
        for node_ in nodes:
            self.all_ids.add(node_.id)
    
    def reg_ping_result(self, node_, status):
        self.status[node_.ip] = status
    
    def print_nodes(self):
        total = {}
        total[STATUS_OK] = 0
        total[STATUS_FAIL] = 0
        total[STATUS_ERROR] = 0
        
        for logdist, nodes in self.nodes:
            print '\nLog Distance = ', logdist
            for node_ in nodes:
                total[self.status[node_.ip]] += 1
                print self.status.get(node_.ip), node_.addr
        print '\nTotal OK/FAIL/ERROR'
        print total