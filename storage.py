from directory_tree import DirectoryTree
from storage_server import StorageServer
import random
from typing import io, List, Dict
from ftplib import all_errors as ftp_errors
import logging

FTP_HOSTS = ['172.17.35.158', '172.17.33.119', '172.17.43.137']
FTP_USERS = ['ftpuser', 'ftpuser', 'ftpuser']
FTP_PASSWORDS = ['ftppassword', 'ftppassword', 'ftppassword']

MONGO_HOST = 'localhost:27017'
MONGO_USER = 'admin'
MONGO_PASSWORD = 'mongo'


class Storage:
    """Class representing storage of a distributed file system."""
    def __init__(self):
        self.directory_tree = DirectoryTree(MONGO_HOST, MONGO_USER, MONGO_PASSWORD)
        self.storage_servers = [StorageServer(ftp_host, ftp_user, ftp_password)
                                for ftp_host, ftp_user, ftp_password
                                in zip(FTP_HOSTS, FTP_USERS, FTP_PASSWORDS)]

    def clear(self):
        """Clear the storage."""
        self.directory_tree.clear()
        for storage_server in self.storage_servers:
            try:
                storage_server.clear()
            except ftp_errors as e:
                logging.error(f'Failed to clear the storage on server '
                              f'{storage_server.host}: {e}')

    def _choose_storage_servers(self):
        return random.sample(self.storage_servers, 2)

    def _get_file_servers(self, path: str, filename: str) -> List[StorageServer]:
        servers = self.directory_tree.get_file_servers(path, filename)
        return [server for server in self.storage_servers if server.host in servers]

    def create_file(self, path: str, filename: str):
        """Create an empty file with the specified path."""
        servers = self._choose_storage_servers()
        self.directory_tree.create_file(path, filename,
                                        [server.host for server in servers])
        for storage_server in servers:
            try:
                storage_server.create_file(path, filename)
            except ftp_errors as e:
                logging.error(f'Failed to create file {filename} on server '
                              f'{storage_server.host}: {e}')

    def write_file(self, path: str, filename: str, file: io):
        """Write a file with the specified path."""
        servers = self._choose_storage_servers()
        self.directory_tree.create_file(path, filename,
                                        [server.host for server in servers])
        for storage_server in servers:
            try:
                storage_server.write_file(path, filename, file)
                file.seek(0)
            except ftp_errors as e:
                logging.error(f'Failed to write file {filename} on server '
                              f'{storage_server.host}: {e}')

    def read_file(self, path: str, filename: str, file: io):
        """Read a file with the specified path."""
        servers = self._get_file_servers(path, filename)
        for storage_server in servers:
            try:
                storage_server.read_file(path, filename, file)
            except ftp_errors as e:
                logging.error(f'Failed to read file {filename} on server '
                              f'{storage_server.host}: {e}')
            else:
                return
        logging.error(f'Failed to read file {filename}')

    def delete_file(self, path: str, filename: str):
        """Delete a file with the specified path."""
        servers = self._get_file_servers(path, filename)
        print(servers)
        self.directory_tree.delete_file(path, filename)
        for storage_server in servers:
            try:
                storage_server.delete_file(path, filename)
            except ftp_errors as e:
                logging.error(f'Failed to delete file {filename} on server '
                              f'{storage_server.host}: {e}')

    def get_file_size(self, path: str, filename: str) -> int:
        """Return the size of a file with the specified path, in bytes."""
        servers = self._get_file_servers(path, filename)
        for storage_server in servers:
            try:
                size = storage_server.get_file_size(path, filename)
            except ftp_errors as e:
                logging.error(f'Failed to get size of file {filename} on server '
                              f'{storage_server.host}: {e}')
            else:
                return size
        logging.error(f'Failed to get size of file {filename}')
        return -1

    def copy_file(self, path: str, filename: str, new_path: str, new_filename: str = None):
        """Copy a file with the specified path to the new path."""
        servers = self._get_file_servers(path, filename)
        self.directory_tree.copy_file(path, filename, new_path, new_filename)
        for storage_server in servers:
            try:
                storage_server.copy_file(path, filename, new_path, new_filename)
            except ftp_errors as e:
                logging.error(f'Failed to copy file {filename} on server '
                              f'{storage_server.host}: {e}')

    def move_file(self, path: str, filename: str, new_path: str, new_filename: str = None):
        """Move a file with the specified path to the new path."""
        servers = self._get_file_servers(path, filename)
        self.directory_tree.move_file(path, filename, new_path, new_filename)
        for storage_server in servers:
            try:
                storage_server.move_file(path, filename, new_path, new_filename)
            except ftp_errors as e:
                logging.error(f'Failed to move file {filename} on server '
                              f'{storage_server.host}: {e}')

    def read_dir(self, path: str) -> List[Dict[str, str]]:
        """Return a list of files which are stored in the directory."""
        return self.directory_tree.read_dir(path)

    def make_dir(self, path: str, dirname: str):
        """Make a new directory with the specified path"""
        self.directory_tree.make_dir(path, dirname)
        for storage_server in self.storage_servers:
            try:
                storage_server.make_dir(path, dirname)
            except ftp_errors as e:
                logging.error(f'Failed to make directory {dirname} on server '
                              f'{storage_server.host}: {e}')

    def delete_dir(self, path: str, dirname: str):
        """Delete a directory with the specified path"""
        self.directory_tree.delete_dir(path, dirname)
        for storage_server in self.storage_servers:
            try:
                storage_server.delete_dir(path, dirname)
            except ftp_errors as e:
                logging.error(f'Failed to delete directory {dirname} on server '
                              f'{storage_server.host}: {e}')


if __name__ == '__main__':
    ss = Storage()

    ss.clear()
    ss.make_dir('', 'dir1')
    ss.make_dir('dir1', 'inner_dir')
    ss.make_dir('', 'dir2')
    ss.create_file('dir1/inner_dir', 'file1')
    ss.create_file('dir1/inner_dir', 'file2')
    ss.create_file('dir1/inner_dir', 'file3')
    print(ss.read_dir('dir1'))
    print(ss.read_dir('dir1/inner_dir'))
    with open('text_file.txt', 'rb') as f:
        ss.write_file('dir2', 'text_file.txt', f)
    with open('read_file.txt', 'wb') as f:
        ss.read_file('dir2', 'text_file.txt', f)
    ss.make_dir('dir2', 'copies')
    print(ss.read_dir('dir2/copies'))
    ss.copy_file('dir2', 'text_file.txt', 'dir2/copies', 'text_file.copy')
    ss.move_file('dir2', 'text_file.txt', 'dir2/copies', 'text_file.copy2')
    print(ss.get_file_size('dir2/copies', 'text_file.copy'))
    print(ss.read_dir('dir2/copies'))
    ss.delete_file('dir2/copies', 'text_file.copy2')
    print(ss.read_dir('dir2/copies'))
    ss.delete_dir('', 'dir2')
    print(ss.read_dir(''))
