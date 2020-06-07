import re
import json
import requests
import hashlib
import base64
import urllib.parse
import logging

import appsecrets


class TPLink(object):
    
    def __init__(self, router_ip='192.168.1.1', secrets=None):
        if secrets:
            self.secrets = secrets
        else:
            self.secrets = appsecrets.CachedSecrets()
        self.ip = router_ip
        self.session = None
        self.session_url_path_prefix = None

    def get_auth(self):
        secrets = appsecrets.CachedSecrets()
        username = secrets.get_password('router.username')
        password = secrets.get_password('router.password')
        return (username, password)

    def make_expected_cookie(self):
        username, password = self.get_auth()
        password_hash = hashlib.md5(password.encode('utf8')).hexdigest()
        authorization_string = username+':'+password_hash
        authorization_b64 = base64.b64encode(authorization_string.encode('utf8'))
        authorization_cookie_string = 'Basic '+authorization_b64.decode('utf8')
        cookie_string = 'Authorization='+urllib.parse.quote(authorization_cookie_string)+';path=/'
        return cookie_string

    def login(self):
        self.session = requests.Session()
        # Leave this here in case they get more clever later.
        #headers = {
        #        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36',
        #        'Accept': '*/*',
        #}
        #self.session.headers.update(headers)
        #self.session.headers.update({'Cookie':'Authorization='})
        #result_homepage = self.session.get(self.url_base())
        #result_homepage.raise_for_status()
        self.session.headers.update({'Cookie':self.make_expected_cookie()})
        url = self.url_base()+'/userRpm/LoginRpm.htm?Save=Save'
        result = self.session.get(url)
        result.raise_for_status()
        content = result.text
        matcher = re.compile('location\\.href = "'+self.url_base()+'/([A-Z]*)/.*\\.htm"')
        url_piece = re.search(matcher, content).groups()[0]
        self.session_url_path_prefix = url_piece
        logging.info('Current session URL path piece: {}'.format(self.session_url_path_prefix))
        return True

    def url_base(self):
        return 'http://'+self.ip

    def get_path(self, path):
        if not self.session_url_path_prefix:
            success = self.login()
            if not (success and self.session_url_path_prefix):
                raise RuntimeError('Failed to get logged in session on firmware.')
        url = '/'.join([self.url_base(), self.session_url_path_prefix, path])
        result = self.session.get(url)
        result.raise_for_status()
        content = result.text
        return content

    def get_client_ips(self):
        content = self.get_path('userRpm/AssignedIpAddrListRpm.htm')
        content_no_newlines = content.replace('\n', '').replace('\r', '')
        first_script, _, _ = content_no_newlines.partition('</SCRIPT>')
        if not 'DHCPDynList' in first_script:
            raise RuntimeError('Failed to parse client list.')
        _, _, approx_array = first_script.partition('DHCPDynList')
        if not (approx_array.startswith(' = new Array(') and approx_array.endswith(');')):
            raise RuntimeError('Failed to parse client list.')
        array_content = approx_array[13:-3]
        array_values = [x.strip('"') for x in array_content.split(', ')][:-1]
        output = []
        keys = ['name', 'mac', 'ip', 'lease_time']
        curr = None
        for i in range(len(array_values)):
            if i % 4 == 0:
                curr = {}
                output.append(curr)
            curr[keys[i%4]] = array_values[i]
        return output


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(TPLink().get_client_ips(), indent=2))
