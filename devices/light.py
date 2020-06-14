import time

from phue import Bridge

from devices import router
import appsecrets


class PhilipsHue(object):

    def __init__(self, router_object=None, router_ip=None, mac_address=None):
        if router_object:
            self.router = router_object
        elif router_ip:
            self.router = router_object(router_ip)
        else:
            raise ValueError('Must provide router or router_ip')
        self.mac_address = mac_address
        self.bridge = Bridge(self.get_bridge_ip()) 

    def get_bridge_ip(self):
        client_list = self.router.get_client_ips()
        name = 'Philips-hue'
        hue_entry = list(filter(lambda x: x['name'] == name, client_list))
        if not hue_entry:
            raise RuntimeError('No entries named {} found in DHCP client list ({} entries checked).'.format(name, len(client_list)))
        if self.mac_address:
            hue_entry = list(filter(lambda x: x['mac'] == self.mac_address, hue_entry))
        if not hue_entry:
            raise RuntimeError('No entries named {} with mac {} found in DHCP client list ({} entries checked).'.format(name, self.mac_address, len(client_list)))
        if len(hue_entry) > 1:
            raise RuntimeError('Found {} entries named {}, consider specifying mac_address in constructor: {}'.format(len(hue_entry), name, hue_entry))
        return hue_entry[0]['ip']


class LivingRoom(PhilipsHue):

    def acknowledge(self):
        group = self.bridge.groups[0]
        sleep_secs = 0.3
        if group.on:
            brightness = group.brightness
            group.brightness = brightness/2.
            time.sleep(sleep_secs)
            group.brightness = brightness
        else:
            group.on = True
            time.sleep(sleep_secs)
            group.on = False


if __name__ == '__main__':
    this_secrets = appsecrets.CachedSecrets()
    this_router = router.TPLink(secrets=this_secrets)
    hue = LivingRoom(this_router)
    hue.acknowledge()
