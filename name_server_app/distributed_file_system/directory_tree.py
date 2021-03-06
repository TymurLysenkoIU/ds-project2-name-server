from pymongo import MongoClient
from typing import List, Dict
import posixpath

__all__ = ['DirectoryTree', 'InvalidPathError', 'NoSuchFileError', 'NoSuchDirectoryError']

HOST = '192.168.31.156:27017'
USER = 'admin'
PASSWORD = 'mongo'


class InvalidPathError(Exception):
    pass


class NoSuchDirectoryError(InvalidPathError):
    pass


class NoSuchFileError(InvalidPathError):
    pass


class DirectoryTree:
    """Class used as client for a MongoDB storing directory tree of a
    distributed file system.

    Arguments:
        host: str - hostname or IP of MongoDB database
        username: str - username for MongoDB database
        password: str - password for MongoDB database
    """
    def __init__(self, host: str, username: str, password: str):
        self.client = MongoClient(host=host, username=username, password=password)
        self.db = self.client.storage
        self.tree = self.db.tree

        if self.tree.count_documents({}) == 0:  # empty tree
            self.root_id = self.tree.insert_one({'type': 'root'}).inserted_id
        else:
            self.root_id = self.tree.find_one({
                'type': 'root'
            })['_id']

    def clear(self):
        """Clear the directory tree."""
        self.tree.delete_many({
            'type': {'$ne': 'root'}
        })

    def create_file(self, path: str, filename: str, servers: List[str]):
        """Create a file in the tree and index servers storing this file."""
        self.tree.insert_one({
            'type': 'file',
            'name': filename,
            'parent': self._get_dir_id_by_path(path),
            'servers': servers,
        })

    def get_file_servers(self, path: str, filename: str) -> List[str]:
        """Return servers storing the file with the specified path"""
        try:
            return self.tree.find_one({
                'type': 'file',
                'name': filename,
                'parent': self._get_dir_id_by_path(path),
            })['servers']
        except TypeError:
            raise NoSuchFileError(f'There is no such file: {posixpath.join(path, filename)}')

    def delete_file(self, path: str, filename: str):
        """Delete a file from the tree."""
        result = self.tree.delete_one({
            'type': 'file',
            'name': filename,
            'parent': self._get_dir_id_by_path(path),
        })
        if result.deleted_count == 0:
            raise NoSuchFileError(f'There is no such file: {posixpath.join(path, filename)}')

    def copy_file(self, path: str, filename: str, new_path: str, new_filename: str = None):
        """Copy a file with the specified path to the new path."""
        try:
            new_filename = new_filename or filename
            servers = self.tree.find_one({
                'type': 'file',
                'name': filename,
                'parent': self._get_dir_id_by_path(path),
            })['servers']
            self.create_file(new_path, new_filename, servers)
        except TypeError:
            raise NoSuchFileError(f'There is no such file: {posixpath.join(path, filename)}')

    def move_file(self, path: str, filename: str, new_path: str, new_filename: str = None):
        """Move a file with the specified path to the new path."""
        self.copy_file(path, filename, new_path, new_filename)
        self.delete_file(path, filename)

    def make_dir(self, path: str, dirname: str):
        """Make a new directory with the specified path."""
        self.tree.insert_one({
            'type': 'dir',
            'name': dirname,
            'parent': self._get_dir_id_by_path(path),
        })

    def read_dir(self, path: str) -> List[Dict[str, str]]:
        """Return list of files and directories stored in the directory."""
        return [
            {key: document[key] for key in ('type', 'name')}
            for document in self.tree.find({
                 'parent': self._get_dir_id_by_path(path),
            })
        ]

    def delete_dir(self, path: str, dirname: str):
        """Delete a directory with the specified path."""
        self._delete_dir(posixpath.join(path, dirname))

    def as_list(self) -> List[Dict[str, str]]:
        """Return directory tree as list of dicts {'path': ..., 'dirname': ...}"""
        dir_list = []
        self._traverse('/', dir_list)
        return dir_list

    def _traverse(self, cur_path: str, dir_list: List[Dict[str, str]]):
        for document in self.read_dir(cur_path):
            if document['type'] == 'dir':
                dir_list.append({'path': cur_path, 'dirname': document['name']})
                self._traverse(posixpath.join(cur_path, document['name']), dir_list)

    def _delete_dir(self, path):
        for document in self.read_dir(path):
            if document['type'] == 'dir':
                self._delete_dir(posixpath.join(path, document['name']))
            elif document['type'] == 'file':
                self.delete_file(path, document['name'])
        self.tree.delete_one({'_id': self._get_dir_id_by_path(path)})

    def _get_dir_id_by_path(self, path: str) -> str:
        try:
            dirs = [dir_ for dir_ in path.split('/') if dir_]
            cur_dir_id = self.root_id
            for dir_ in dirs:
                cur_dir_id = self.tree.find_one({
                    'type': 'dir',
                    'name': dir_,
                    'parent': cur_dir_id
                })['_id']
            return cur_dir_id
        except TypeError:
            raise NoSuchDirectoryError(f'There is no such directory: {path}')


if __name__ == '__main__':
    dt = DirectoryTree(HOST, USER, PASSWORD)
    dt.clear()

    dt.make_dir('', 'dir1')
    dt.make_dir('dir1', 'inner_dir')
    dt.make_dir('', 'dir2')
    dt.create_file('dir1/inner_dir', 'file1', ['ss1', 'ss2'])
    dt.create_file('dir1/inner_dir', 'file2', ['ss1', 'ss3'])
    dt.create_file('dir1/inner_dir', 'file3', ['ss2', 'ss3'])
    print(dt.read_dir('dir1'))
    print(dt.read_dir('dir1/inner_dir'))
    dt.create_file('dir2', 'text_file.txt', ['ss1', 'ss3'])
    dt.make_dir('dir2', 'copies')
    dt.copy_file('dir2', 'text_file.txt', 'dir2/copies', 'text_file.copy')
    dt.move_file('dir2', 'text_file.txt', 'dir2/copies', 'text_file.copy2')
    print(dt.as_list())
    print(dt.read_dir('dir2/copies'))
    dt.delete_file('dir2/copies', 'text_file.copy2')
    print(dt.read_dir('dir2/copies'))
    dt.delete_dir('', 'dir2')
    print(dt.read_dir(''))



