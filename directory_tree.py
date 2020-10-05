from pymongo import MongoClient
from typing import List, Dict
import posixpath


HOST = 'localhost:27017'
USER = 'admin'
PASSWORD = 'mongo'


class DirectoryTree:
    def __init__(self, db: MongoClient):
        self.db = db
        self.tree = self.db.tree

        print(self.tree.count_documents({}))

        if self.tree.count_documents({}) == 0:  # empty tree
            self.root_id = self.tree.insert_one({'type': 'root'}).inserted_id
        else:
            self.root_id = self.tree.find_one({
                'type': {'$ne': 'root'}
            })['_id']

    def clear(self):
        """Clear the directory tree."""
        self.tree.delete_many({})

    def create_file(self, path: str, filename: str, servers: List[str]):
        """Create a file in the tree and index servers storing this file."""
        self.tree.insert_one({
            'type': 'file',
            'name': filename,
            'parent': self._get_dir_id_by_path(path),
            'servers': servers,
        })

    def delete_file(self, path: str, filename: str):
        """Delete a file from the tree."""
        self.tree.delete_one({
            'type': 'file',
            'name': filename,
            'parent': self._get_dir_id_by_path(path),
        })

    def copy_file(self, path: str, filename: str, new_path: str, new_filename: str = None):
        """Copy a file with the specified path to the new path."""
        new_filename = new_filename or filename
        servers = self.tree.find_one({
            'type': 'file',
            'name': filename,
            'parent': self._get_dir_id_by_path(path),
        })['servers']
        self.create_file(new_path, new_filename, servers)

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
        """Return list of files and directories stored in a file."""
        return [
            {key: document[key] for key in ('type', 'name')}
            for document in self.tree.find({
                 'parent': self._get_dir_id_by_path(path),
            })
        ]

    def delete_dir(self, path: str, dirname: str):
        """Delete a directory with the specified path."""
        self._delete_dir(posixpath.join(path, dirname))

    def _delete_dir(self, path):
        for document in self.read_dir(path):
            if document['type'] == 'dir':
                self._delete_dir(posixpath.join(path, document['name']))
            elif document['type'] == 'file':
                self.delete_file(path, document['name'])
        self.tree.delete_one({'_id': self._get_dir_id_by_path(path)})

    def _get_dir_id_by_path(self, path: str) -> str:
        dirs = [dir_ for dir_ in path.split('/') if dir_]
        cur_dir_id = self.root_id
        for dir_ in dirs:
            cur_dir_id = self.tree.find_one({
                'type': 'dir',
                'name': dir_,
                'parent': cur_dir_id
            })['_id']
        return cur_dir_id


if __name__ == '__main__':
    client = MongoClient(host=HOST, username=USER, password=PASSWORD)
    dt = DirectoryTree(client.storage)
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
    print(dt.read_dir('dir2/copies'))
    dt.delete_file('dir2/copies', 'text_file.copy2')
    print(dt.read_dir('dir2/copies'))
    dt.delete_dir('', 'dir2')
    print(dt.read_dir(''))



