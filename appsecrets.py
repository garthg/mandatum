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
            raise ValueError(self.get_interactive_instructions(username))
        return data[username]
    
    def set_password(self, username, password):
        self.read_cache()  # Do this to make sure self.data is fresh (not thread safe...)
        self.data[username] = password
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


def get_password(username):
    secrets = CachedSecrets()
    password = secrets.get_password(username)
    return password


def set_password(username, password):
    secrets = CachedSecrets()
    secrets.set_password(username, password)


if __name__ == '__main__':
    args = sys.argv
    usage = 'Usage: {} get|set <key>'.format(args[0])
    if args:
        if not len(args) == 3:
            print(usage)
            sys.exit(11)
        command = args[1]
        username = args[2]
        if command == 'get':
            print(get_password(username))
        elif command == 'set':
            print('At password prompt, enter value for key: {}'.format(username))
            password = getpass()
            set_password(username, password)
            print('Value stored in encrypted file: {}'.format(os.path.abspath(CachedSecrets().filepath)))
        else:
            print(usage)
            sys.exit(11)
