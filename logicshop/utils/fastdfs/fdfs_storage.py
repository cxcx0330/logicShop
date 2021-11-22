# @Time: 2021/11/21-10:17
# @User: Ycx
from django.conf import settings
from django.core.files.storage import Storage


class FastDFSStorage(Storage):
    """自定义文件存储类"""

    def __init__(self, fast_base_url=None):
        # if not fast_base_url:
        #     self.fast_base_url = settings.FAST_BASE_URL
        # self.fast_base_url = fast_base_url
        self.fast_base_url = fast_base_url or settings.FAST_BASE_URL

    # 必须添加open 与 save 方法
    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        pass

    def url(self, name):
        """
        返回文件路径
        :param name:文件路径
        :return:ip+port+文件路径
        """
        return self.fast_base_url + name
