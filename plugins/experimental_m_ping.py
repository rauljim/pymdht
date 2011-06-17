
import core.message





class ExperimentalManager:
    
    def __init__(self):
        #TODO data structure to keep track of things
        pass
        
            
    def on_query_received(self, msg):
        if 1:#msg.query == message.PING:
            print 'experimental got query (%s) from %r' % (msg.query, msg.src_node)
#            return message.OutgoingPingResponse(msg.src_node, self._my_id)
        
    def on_response_received(self, node_, msg):
        pass
           
        
        
        
        