import sys
import os
import json
from getpass import getpass
import keyring
import simplecrypt
import string
import secrets


class CachedSecrets(object):
    APPLICATION_ID = 'mandatum_python_application'
    
    def __init__(self, filepath='secrets.json.aes'):
        self.filepath = filepath
        self.data = None

    def generate_random_password(self, length=32):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(length))

    def get_or_create_system_password(self):
        password = self.get_system_password()
        if not password:
            password = self.generate_random_password()
            self.set_system_password(password)
        return password

    def read_cache(self):
        if self.data is None:
            self.data = {}
            if os.path.isfile(self.filepath):
                with open(self.filepath, 'rb') as fid:
                    data_cipher = fid.read()
                    if data_cipher:
                        data_string = simplecrypt.decrypt(self.get_or_create_system_password(), data_cipher)
                        data = json.loads(data_string)
                        self.data = data
        return self.data

    def write_cache(self):
        if self.data is not None:
            with open(self.filepath, 'wb') as fid:
                data_string = json.dumps(self.data)
                data_cipher = simplecrypt.encrypt(self.get_or_create_system_password(), data_string)
                fid.write(data_cipher)

    def get_password(self, username):
        data = self.read_cache()
        if not username in data:
            raise ValueError('No entry for {} in encrypted file: {}'.format(username, self.filepath))
        return data[username]
    
    def set_password(self, username, password):
        self.read_cache()  # Do this to make sure self.data is fresh (not thread safe...)
        self.data[username] = password
        self.write_cache()

    def get_system_password(self):
        result = keyring.get_password(self.APPLICATION_ID, str(self.__class__))
        return result

    def set_system_password(self, password):
        keyring.set_password(self.APPLICATION_ID, str(self.__class__), password)


def get_password(username):
    secrets = CachedSecrets()
    try:
        password = secrets.get_password(username)
    except ValueError:
        raise ValueError('No password for "{}": run `python {} set {}` and follow prompts.'.format(username, sys.argv[0], username))
    return password


def set_password(username, password):
    secrets = CachedSecrets()
    secrets.set_password(username, password)


if __name__ == '__main__':
    args = sys.argv
    usage = 'Usage: {} get|set <username>'.format(args[0])
    if args:
        if not len(args) == 3:
            print(usage)
            sys.exit(11)
        command = args[1]
        username = args[2]
        if command == 'get':
            print(get_password(username))
        elif command == 'set':
            print('Enter password for {}'.format(username))
            password = getpass()
            set_password(username, password)
        else:
            print(usage)
            sys.exit(11)
