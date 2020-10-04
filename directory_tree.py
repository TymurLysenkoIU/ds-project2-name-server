from pymongo import MongoClient
from typing import List


HOST = 'localhost:27017'
USER = 'admin'
PASSWORD = 'mongo'


class DirectoryTree:
    def __init__(self, db: MongoClient, storage_servers: List[str]):
        self.db = db
        self.tree = self.db.tree
        self.storage_servers = storage_servers

        if self.tree.count_documents({}) == 0:  # empty tree
            self.root_id = self.tree.insert_one({'type': 'root'}).inserted_id
        else:
            self.root_id = self.tree.find_one({'type': 'root'})['_id']

    def clear(self):
        """Clear the directory tree"""
        self.tree.delete_many({})

    def make_dir(self, path: str, dirname: str):
        """Make a new directory with the specified path"""
        self.tree.insert_one({
            'type': 'dir',
            'name': dirname,
            'parent': self._get_dir_id_by_path(path),
        })

    def delete_dir(self, path: str, dirname: str):
        """Delete a directory with the specified path"""
        pass

    def _get_dir_id_by_path(self, path: str):
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
    dt = DirectoryTree(client.storage, ['ss1', 'ss2', 'ss3'])
    dt.clear()
    dt.make_dir('', 'dir1')
    dt.make_dir('dir1', 'dir2')
    dt.make_dir('dir1/dir2', 'dir3')

