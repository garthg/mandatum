import sys
import os
import json
from getpass import getpass
import keyring
from cryptography.fernet import Fernet
import string
import secrets


class CachedSecrets(object):
    APPLICATION_ID = 'mandatum_python_application'
    
    def __init__(self, filepath='secrets.json.aes'):
        self.filepath = filepath
        self.data = None

    def get_or_create_system_crypto_suite(self):
        password_bytes = None
        password = self.get_system_password()
        if not password:
            password_bytes = Fernet.generate_key()
            password = password_bytes.decode('utf8')
            self.set_system_password(password)
        else:
            password_bytes = password.encode('utf8')
        return Fernet(password_bytes)

    def read_cache(self):
        if self.data is None:
            self.data = {}
            if os.path.isfile(self.filepath):
                with open(self.filepath, 'rb') as fid:
                    data_cipher = fid.read()
                    if data_cipher:
                        data_string = self.get_or_create_system_crypto_suite().decrypt(data_cipher)
                        data = json.loads(data_string)
                        self.data = data
        return self.data

    def write_cache(self):
        if self.data is not None:
            with open(self.filepath, 'wb') as fid:
                data_string = json.dumps(self.data)
                data_cipher = self.get_or_create_system_crypto_suite().encrypt(data_string.encode('utf8'))
                fid.write(data_cipher)

    def get_password(self, username):
        data = self.read_cache()
        if not username in data:
            raise ValueError(self.get_interactive_instructions(username))
        return data[username]
    
    def set_password(self, name, password):
        self.read_cache()  # Do this to make sure self.data is fresh (not thread safe...)
        self.data[name] = password
        self.write_cache()

    def get_system_username(self):
        return os.path.abspath(self.filepath)

    def get_system_password(self):
        result = keyring.get_password(self.APPLICATION_ID, self.get_system_username())
        return result

    def set_system_password(self, password):
        keyring.set_password(self.APPLICATION_ID, self.get_system_username(), password)

    def get_interactive_instructions(self, username):
        return 'No entry for "{username}" in cache, to set interactively run `python {filename} set {username}` and follow prompts.'.format(
                username=username, filename=__file__)


def get_password(name):
    secrets = CachedSecrets()
    password = secrets.get_password(name)
    return password


def set_password(name, password):
    secrets = CachedSecrets()
    secrets.set_password(name, password)


def get_password_keys():
    secrets = CachedSecrets()
    keys = secrets.read_cache().keys()
    return keys


if __name__ == '__main__':
    args = sys.argv
    usage = 'Usage: {} get|set|list [<key>]'.format(args[0])
    if args:
        if not len(args) >= 2:
            print(usage)
            sys.exit(11)
        command = args[1]
        if command == 'get':
            name = args[2]
            print(get_password(name))
        elif command == 'set':
            name = args[2]
            print('At password prompt, enter value for: {}'.format(name))
            password = getpass()
            set_password(name, password)
            print('Value stored in encrypted file: {}'.format(os.path.abspath(CachedSecrets().filepath)))
        elif command == 'list':
            print('\n'.join(sorted(get_password_keys())))
        else:
            print(usage)
            sys.exit(11)
