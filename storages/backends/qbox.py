import os
import mimetypes

from django.core.files.storage import Storage
from django.core.files.base import File

from qbox import config
from qbox.connection import QboxConnection
from qbox.service import QboxService
from qbox import uptoken, rscli

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class QboxStorage(Storage):
    def __init__(self, bucket=config.QBOX_BUCKET_NAME, access_key=config.ACCESS_KEY, secret_key=config.SECRET_KEY):
        self.connection = self._get_connection(access_key, secret_key)
        self.bucket = self._get_or_create_bucket(bucket)
        self.service = self._get_service()

    def _get_or_create_bucket(self, name):
        """获取bucket，如果没有就创建一个"""
        if name not in self.service.Buckets():
            name = self.service.Mkbucket(name)
        return name

    def _get_connection(self, access_key, secret_key):
        return QboxConnection(access_key, secret_key)

    def _get_service(self):
        return QboxService(self.connection, self.bucket)

    def _clean_name(self, name):
        """
        更改文件路径使得兼容windows
        """
        return os.path.normpath(name).replace('\\', '/')

    def _open(self, name, mode='rb'):
        name = self._clean_name(name)
        remote_file = QboxStorageFile(name, self, mode=mode)
        return remote_file

    def _read(self, name, start_range=None, end_range=None):
        pass

    def _save(self, name, content):
        return self._upload_file(name, content)

    def _upload_file(self, name, content):
        tokenObj = uptoken.UploadToken(self.bucket, 3600)
        uploadToken = tokenObj.geterate_token()
        content_type = getattr(content, 'content_type',
            mimetypes.guess_type(name)[0] or '')
        rscli.UploadFile(self.bucket, name, content_type, content, '', '', uploadToken)

    def delete(self, name):
        """
        删除文件
        """
        self.service.Delete(name)

    def exists(self, name):
        """
        文件是否存在
        """
        resp = self.service.Stat(name)
        if resp == True:
            return False
        else:
            return resp.fsize > 0

    def size(self, name):
        """
        文件大小
        """
        resp = self.service.Stat(name)
        return resp['fsize']

    def url(self, name):
        pass

    def listdir(self, name):
        pass

    def modified_time(self, name):
        resp = self.service.Stat(name)
        return resp['putTime']

    def get_available_name(self, name):
        """覆盖同名文件"""
        if config.FILE_OVERWRITE:
            name = self._clean_name(name)
            return name
        return super(QboxStorage, self).get_available_name(name)


class QboxStorageFile(File):
    def __init__(self, name, storage, mode):
        self._name = name
        self._storage = storage
        self._mode = mode
        self._is_dirty = False
        self.file = StringIO()
        self.start_range = 0

    @property
    def size(self):
        if not hasattr(self, '_size'):
            self._size = self._storage.size(self._name)
        return self._size

    def read(self, num_bytes=None):
        if num_bytes is None:
            args = []
            self.start_range = 0
        else:
            args = [self.start_range, self.start_range + num_bytes - 1]
        data, etags, content_range = self._storage._read(self._name, *args)
        if content_range is not None:
            current_range, size = content_range.split(' ', 1)[1].split('/', 1)
            starg_range, end_range = current_range.split('-', 1)
            self._size, self.start_range = int(size), int(end_range) + 1
        self.file = StringIO(data)
        return self.file.getvalue()
    
    def write(self, content):
        if 'w' not in self._mode:
            raise AttributeError("File was opened for read-only access.")
        self.file = StringIO(content)
        self._is_dirty = True
    
    def close(self):
        if self._is_dirty:
            self._storage._put_file(self._name, self.file.getvalue())
        self.file.close()


