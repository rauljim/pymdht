
import core.message as message
from core.node import Node
import core.ptime as time




class ExperimentalManager:
    
    def __init__(self, my_id):
        self.my_id = my_id
        self._stop = False
        #TODO data structure to keep track of things
        pass
        
         
    def on_query_received(self, msg):
            
        if not self._stop and msg.query =='find_node':
            self._stop = True
            print 'experimental got query (%s) ' % (msg.query)
            print 'from node  %r' % ( msg.src_node)
            probe_query = message.OutgoingPingQuery(msg.src_node,
                                                    self.my_id,
                                                    ExpObj('aa'))
            print 'Got ping query at time :', time.time()
            return [probe_query]
        return []
       #zinat call a function that send the ping  to the source node again
                         
                 
        
    def on_response_received(self, msg, related_query):
        if related_query.experimental_obj:
            print "probe OK", related_query.experimental_obj.value
        pass
           
    def on_timeout(self, related_query):
        if related_query.experimental_obj:
            print 'prove FAILED', related_query.experimental_obj.value
            
            
class ExpObj:
    def __init__(self, value):
        self.value = value
        self.query_ts = time.time()
        pass
            
        
        