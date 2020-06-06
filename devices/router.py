from urllib import request

import appsecrets


class TPLink(object):
    
    def __init__(self, router_ip='192.168.1.1', secrets=None):
        if secrets:
            self.secrets = secrets
        else:
            self.secrets = appsecrets.CachedSecrets()
        self.ip = router_ip
        self.auth_initialized = False

    def setup_auth(self):
        if self.auth_initialized:
            return
        username = self.secrets.get_password('router.username')
        password = self.secrets.get_password('router.password')
        password_manager = request.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(None, self.url_base(), username, password)
        request.install_opener(request.build_opener(request.HTTPBasicAuthHandler(password_manager)))
        self.auth_initialized = True

    def url_base(self):
        return 'http://'+self.ip

    def get_path(self, path):
        self.setup_auth()
        url = self.url_base()+path
        content = request.urlopen(url).read()
        return content

    def get_client_ips(self):
        content = self.get_path('/userRpm/AssignedIpAddrListRpm.htm')
        print(content)
        import pdb; pdb.set_trace()


if __name__ == '__main__':
    print(TPLink().get_client_ips())
