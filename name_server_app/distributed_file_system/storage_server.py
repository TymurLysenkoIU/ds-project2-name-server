from ftplib import FTP, all_errors
from io import BytesIO
import posixpath
from tempfile import TemporaryFile
from typing import io, List

__all__ = ['StorageServer']

HOST = '192.168.31.159'
USER = 'ftpuser'
PASSWORD = 'ftp-pass'


class StorageServer:
    """
    Class used as client for a FTP server on a storage.

    Arguments:
        host
    """
    STORAGE_DIR = '/'

    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.ftp = FTP(host)
        # self.ftp.set_pasv(False)
        # self.ftp.set_debuglevel(1)
        self.ftp.login(username, password)

    def _change_dir(self, path):
        path = path.lstrip('/')
        self.ftp.cwd(posixpath.join(self.STORAGE_DIR, path))

    def create_file(self, path: str, filename: str):
        """Create an empty file with the specified path."""
        self._change_dir(path)
        self.ftp.storbinary(f'STOR {filename}', BytesIO())

    def read_file(self, path: str, filename: str, file: io):
        """Read a file with the specified path."""
        self._change_dir(path)
        self.ftp.retrbinary(f'RETR {filename}', file.write)

    def write_file(self, path: str, filename: str, file: io):
        """Write a file with the specified path."""
        self._change_dir(path)
        self.ftp.storbinary(f'STOR {filename}', file)

    def delete_file(self, path: str, filename: str):
        """Delete a file with the specified path."""
        self._change_dir(path)
        self.ftp.delete(filename)

    def get_file_size(self, path: str, filename: str) -> int:
        """Return the size of a file with the specified path, in bytes."""
        self._change_dir(path)
        return self.ftp.size(filename)

    def copy_file(self, path: str, filename: str, new_path: str, new_filename: str = None):
        """Copy a file with the specified path to the new path."""
        new_filename = new_filename or filename
        with TemporaryFile() as file:
            self.read_file(path, filename, file)
            file.seek(0)
            self.write_file(new_path, new_filename, file)

    def move_file(self, path: str, filename: str, new_path: str, new_filename: str = None):
        """Move a file with the specified path to the new path."""
        self.copy_file(path, filename, new_path, new_filename)
        self.delete_file(path, filename)

    def read_dir(self, path: str) -> List[str]:
        """Return a list of files which are stored in the directory."""
        self._change_dir(path)
        return list(self.ftp.nlst())

    def make_dir(self, path: str, dirname: str):
        """Make a new directory with the specified path"""
        self._change_dir(path)
        self.ftp.mkd(dirname)

    def delete_dir(self, path: str, dirname: str):
        """Delete a directory with the specified path"""
        self._delete_dir(posixpath.join(self.STORAGE_DIR, posixpath.join(path, dirname)))

    def _delete_dir(self, path):
        """Recursively delete a folder and all files in it."""
        for name in self.ftp.nlst(path):
            try:
                self.ftp.cwd(name)  # it won't cause an error if it's a folder
                self._delete_dir(posixpath.join(path, name))
            except all_errors:
                self.ftp.delete(posixpath.join(path, name))

        self.ftp.rmd(path)

    def clear(self):
        """Clear the storage."""
        for name in self.ftp.nlst(self.STORAGE_DIR):
            try:
                self.ftp.cwd(name)
                self._delete_dir(posixpath.join(self.STORAGE_DIR, name))
            except all_errors:
                self.ftp.delete(posixpath.join(self.STORAGE_DIR, name))

    def __repr__(self):
        return f'StorageServer(host={self.host})'


if __name__ == '__main__':
    ss = StorageServer(HOST, USER, PASSWORD)

    ss.clear()
    ss.make_dir('/', 'dir1')
    ss.make_dir('dir1', 'inner_dir')
    ss.make_dir('/', 'dir2')
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
    print(ss.read_dir('dir2/copies'))
    print(ss.get_file_size('dir2/copies', 'text_file.copy'))
    ss.delete_file('dir2/copies', 'text_file.copy2')
    print(ss.read_dir('dir2/copies'))
    ss.delete_dir('', 'dir2')
    print(ss.read_dir(''))
    ss.clear()
    print(ss.read_dir(''))
