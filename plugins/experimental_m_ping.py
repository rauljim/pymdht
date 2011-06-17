
import core.message





class pingManager:
    
    def __init__(self, msg):
        
        self.msg=msg
        
            
    def get_ping_response(self, msg):
        if msg.query == message.PING:
            return message.OutgoingPingResponse(msg.src_node, self._my_id)
        
            
           
        
        
        
        