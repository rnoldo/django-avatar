# -*- encoding:utf-8 -*-

__author__ = 'rnoldo@gmail.com(nerdyang.com)'

import httplib2
import hmac
import urllib
from urlparse import urlparse
from hashlib import sha1
from base64 import urlsafe_b64encode
try:
    import json
except ImportError:
    import simplejson as json


class QboxError(Exception):
	pass


class QboxConnection(object):
    def __init__(self, access_key=None, secret_key=None):
        self.access_key = access_key
        self.secret_key = secret_key

    def generate_access_token(self, url, params=None):
        """
         请求签名
         1、认证授权主要是对客户方的请求进行数字签名，签名运算分为如下几个步骤：
         2、分解请求的URL，从中分离得出 path 和 query_string 的内容；
         3、用字符串拼接的方式组装 path 和 query_string，两者之间以 ? 连接；
         4、在以上连接后的字符串末尾添加一个换行符 "\n"；
         5、如果存在 form 表单形式的参数，将这些参数序列化为 query_string 形式的字符串；
         6、在原来已拼接的字符串基础上再添加表单参数序列化后的字符串；
         7、用 hmac/sha1 进行签名，其中参数一 SECRET_KEY 为私钥，参数二是已拼接的字符串为要签名的数据本身；
         8、对签名后得到的 digest 进行URL安全形式的base64编码；
         9、用 access_key 明文与编码后的 digest 进行拼接，中间使用冒号 : 连接，得到一个总的 access_token；
       """
        parsedurl = urlparse(url)
        query = parsedurl.query
        path = parsedurl.path
        if query:
            path = ''.join([path, '?', query])
        path = ''.join([path, "\n"])
        if params:
            path = ''.join([path, params])

        hashed = hmac.new(self.secret_key, path, sha1)
        return "%s:%s" % (self.access_key, urlsafe_b64encode(hashed.digest()))

    def make_request(self, url):
        """
         将以上generate_access_token的最终结果（access_token）
         附加到所在请求的 HTTP Headers 中即可，如下示例子，
         在 HTTP Headers 中新增一个名为 Authorization 的字段，
         并将 QBox access_token 作为该字段的值，并根据url和params发起请求
        """
        headers = {}
        token = self.generate_access_token(url)
        headers['Authorization'] = 'Qbox %s' % (token)
        resp, content = httplib2.Http('').request(url, 'POST', '', headers=headers)
        code = resp['status']
        if code != '200':
            raise QboxError("QboxConnection 请求失败 原因 %s %s" % code, content)
        json.loads(content)

    def make_request_with_form(self, url, params=None):
        headers = {}
        encoded_params = urllib.urlencode(params)
        token = self.generate_access_token(url, encoded_params)

        headers['Authorization'] = 'Qbox %s' % (token)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

        resp, content = httplib2.Http('').request(url, 'POST', encoded_params, headers=headers)
        code = resp['status']
        if code != '200':
            raise QboxError("QboxConnection 请求失败 原因 %s %s" % code, content)
        if len(content) != 0:
            json.loads(content)
        return True

