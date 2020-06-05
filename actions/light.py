from phue import Bridge



class LivingRoom(object):

    def __init__(self):
       self.bridge = Bridge(self.get_bridge_ip()) 

    def get_bridge_ip(self):
        return NotImplementedError
