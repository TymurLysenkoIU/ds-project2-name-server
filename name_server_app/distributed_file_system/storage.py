import random
from typing import io, List, Dict
from ftplib import all_errors as ftp_errors
import logging
import sys

from name_server_proj.settings import MONGO_HOST, MONGO_USER, MONGO_PASSWORD, FTP_USERNAME, FTP_PASSWORD
from .directory_tree import DirectoryTree
from .storage_server import StorageServer
from ..helpers import ping, request_space_available

__all__ = ['Storage', 'NoServersAvailable']

FTP_HOSTS = ['192.168.31.157', '192.168.31.158', '192.168.31.159']

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format='%(levelname)s: %(message)s')


class NoServersAvailable(Exception):
    pass


class Storage(object):
    """Singleton class representing storage of a distributed file system."""

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Storage, cls).__new__(cls)
            logging.info('Connecting to MongoDB.')
            cls.instance.directory_tree = DirectoryTree(MONGO_HOST, MONGO_USER, MONGO_PASSWORD)
            logging.info('Successfully connected to MongoDB.')
            cls.instance.storage_servers = []
        return cls.instance

    def _available_servers(self) -> List[str]:
        """Return available servers."""
        return [server for server in self.storage_servers if ping(server)]

    def _choose_storage_servers(self) -> List[str]:
        """Choose storage server for a new file."""
        servers = self._available_servers()
        if len(servers) == 0:
            raise NoServersAvailable('No storage servers are available.')
        if len(servers) > 2:
            return random.sample(servers, 2)
        else:
            return servers

    def _get_file_servers(self, path: str, filename: str) -> List[str]:
        """Return file servers storing the specified file."""
        return self.directory_tree.get_file_servers(path, filename)

    def get_available_space(self):
        """Returns how many bytes are available in storage."""
        total = 0
        for server in self._available_servers():
            total += request_space_available(server)
        return total // 2

    def clear(self):
        """Clear the storage."""
        self.directory_tree.clear()
        for server in self.storage_servers:
            try:
                storage_server = StorageServer(server, FTP_USERNAME, FTP_PASSWORD)
                storage_server.clear()
            except ftp_errors as e:
                logging.error(f'Failed to clear the storage on server '
                              f'{server}: {e}')

    def add_storage_server(self, server: str):
        """Add storage server to the distributed file system."""
        if server not in self.storage_servers:
            self.storage_servers.append(server)

        try:
            storage_server = StorageServer(server, FTP_USERNAME, FTP_PASSWORD)
            storage_server.clear()
        except ftp_errors as e:
            logging.error(f'Failed to clear the storage on server '
                          f'{server}: {e}')

        self.create_dirs(server)

    def create_file(self, path: str, filename: str):
        """Create an empty file with the specified path."""
        servers = self._choose_storage_servers()
        self.directory_tree.create_file(path, filename, servers)
        for server in servers:
            try:
                storage_server = StorageServer(server, FTP_USERNAME, FTP_PASSWORD)
                storage_server.create_file(path, filename)
            except ftp_errors as e:
                logging.error(f'Failed to create file {filename} on server '
                              f'{server}: {e}')

    def write_file(self, path: str, filename: str, file: io):
        """Write a file with the specified path."""
        servers = self._choose_storage_servers()
        self.directory_tree.create_file(path, filename, servers)
        for server in servers:
            try:
                storage_server = StorageServer(server, FTP_USERNAME, FTP_PASSWORD)
                storage_server.write_file(path, filename, file)
                file.seek(0)
            except ftp_errors as e:
                logging.error(f'Failed to write file {filename} on server '
                              f'{server}: {e}')

    def read_file(self, path: str, filename: str, file: io):
        """Read a file with the specified path."""
        servers = self._get_file_servers(path, filename)
        for server in servers:
            try:
                storage_server = StorageServer(server, FTP_USERNAME, FTP_PASSWORD)
                storage_server.read_file(path, filename, file)
                file.seek(0)
            except ftp_errors as e:
                logging.error(f'Failed to read file {filename} on server '
                              f'{server}: {e}')
            else:
                return
        logging.error(f'Failed to read file {filename}')

    def delete_file(self, path: str, filename: str):
        """Delete a file with the specified path."""
        servers = self._get_file_servers(path, filename)
        self.directory_tree.delete_file(path, filename)
        for server in servers:
            try:
                storage_server = StorageServer(server, FTP_USERNAME, FTP_PASSWORD)
                storage_server.delete_file(path, filename)
            except ftp_errors as e:
                logging.error(f'Failed to delete file {filename} on server '
                              f'{server}: {e}')

    def get_file_size(self, path: str, filename: str) -> int:
        """Return the size of a file with the specified path, in bytes."""
        servers = self._get_file_servers(path, filename)
        for server in servers:
            try:
                storage_server = StorageServer(server, FTP_USERNAME, FTP_PASSWORD)
                size = storage_server.get_file_size(path, filename)
            except ftp_errors as e:
                logging.error(f'Failed to get size of file {filename} on server '
                              f'{server}: {e}')
            else:
                return size
        logging.error(f'Failed to get size of file {filename}')
        return -1

    def copy_file(self, path: str, filename: str, new_path: str, new_filename: str = None):
        """Copy a file with the specified path to the new path."""
        servers = self._get_file_servers(path, filename)
        self.directory_tree.copy_file(path, filename, new_path, new_filename)
        for server in servers:
            try:
                storage_server = StorageServer(server, FTP_USERNAME, FTP_PASSWORD)
                storage_server.copy_file(path, filename, new_path, new_filename)
            except ftp_errors as e:
                logging.error(f'Failed to copy file {filename} on server '
                              f'{server}: {e}')

    def move_file(self, path: str, filename: str, new_path: str, new_filename: str = None):
        """Move a file with the specified path to the new path."""
        servers = self._get_file_servers(path, filename)
        self.directory_tree.move_file(path, filename, new_path, new_filename)
        for server in servers:
            try:
                storage_server = StorageServer(server, FTP_USERNAME, FTP_PASSWORD)
                storage_server.move_file(path, filename, new_path, new_filename)
            except ftp_errors as e:
                logging.error(f'Failed to move file {filename} on server '
                              f'{server}: {e}')

    def read_dir(self, path: str) -> List[Dict[str, str]]:
        """Return a list of files which are stored in the directory."""
        return self.directory_tree.read_dir(path)

    def make_dir(self, path: str, dirname: str):
        """Make a new directory with the specified path"""
        self.directory_tree.make_dir(path, dirname)
        for server in self.storage_servers:
            try:
                storage_server = StorageServer(server, FTP_USERNAME, FTP_PASSWORD)
                storage_server.make_dir(path, dirname)
            except ftp_errors as e:
                logging.error(f'Failed to make directory {dirname} on server '
                              f'{server}: {e}')

    def delete_dir(self, path: str, dirname: str):
        """Delete a directory with the specified path"""
        self.directory_tree.delete_dir(path, dirname)
        for server in self.storage_servers:
            try:
                storage_server = StorageServer(server, FTP_USERNAME, FTP_PASSWORD)
                storage_server.delete_dir(path, dirname)
            except ftp_errors as e:
                logging.error(f'Failed to delete directory {dirname} on server '
                              f'{server}: {e}')

    def create_dirs(self, server: str):
        """Create directories from the directory tree on the specified storage server."""
        storage_server = StorageServer(server, FTP_USERNAME, FTP_PASSWORD)
        for dir_dict in self.directory_tree.as_list():
            try:
                storage_server.make_dir(dir_dict['path'], dir_dict['dirname'])
            except ftp_errors as e:
                logging.error(f'Failed to make directory {dir_dict["dirname"]} on server '
                              f'{server}: {e}')


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
