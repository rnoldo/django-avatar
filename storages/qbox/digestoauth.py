# -*- encoding: utf-8 -*-

"""A simple client library to work with Digest Oauth APIs."""

__author__ = 'stevenle08@gmail.com (Steven Le); xushiwei@qbox.net'


import config
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


class Error(Exception):
    pass


class Client(object):
    def Call(self, url, access_key, secret_key):
        # 将以上generate_access_token的最终结果（access_token）
        # 附加到所在请求的 HTTP Headers 中即可，如下示例子，
        # 在 HTTP Headers 中新增一个名为 Authorization 的字段，并将 QBox access_token 作为该字段的值：
        headers = {}
        token = self.generate_access_token(access_key, secret_key, url)
        headers['Authorization'] = 'QBox %s' % (token)
        resp, content = httplib2.Http('').request(url, 'POST', '', headers=headers)

        code = resp['status']
        if code != '200':
            raise Error('DigestOauthRequest.Call failed. Error was: %s %s' % (code, content))
        if len(content) != 0:
            return json.loads(content)
        return True

    def CallNoRet(self, url, access_key, secret_key):
        headers = {}
        token = self.generate_access_token(access_key, secret_key, url)
        headers['Authorization'] = 'QBox %s' % (token)
        resp, content = httplib2.Http('').request(url, 'POST', '', headers=headers)

        code = resp['status']
        if code != '200':
            raise Error('DigestOauthRequest.Call failed. Error was: %s %s' % (code, content))
        return True

    """
      请求签名
      1、认证授权主要是对客户方的请求进行数字签名，签名运算分为如下几个步骤：
      2、分解请求的URL，从中分离得出 path 和 query_string 的内容；
      3、用字符串拼接的方式组装 path 和 query_string，两者之间以 ? 连接；
      4、在以上连接后的字符串末尾添加一个换行符 \n；
      5、如果存在 form 表单形式的参数，将这些参数序列化为 query_string 形式的字符串；
      6、在原来已拼接的字符串基础上再添加表单参数序列化后的字符串；
      7、用 hmac/sha1 进行签名，其中参数一 SECRET_KEY 为私钥，参数二是已拼接的字符串为要签名的数据本身；
      8、对签名后得到的 digest 进行URL安全形式的base64编码；
      9、用 access_key 明文与编码后的 digest 进行拼接，中间使用冒号 : 连接，得到一个总的 access_token；
    """
    def generate_access_token(self, access_key, secret_key, url, params=None):
        parsedurl = urlparse(url)
        query = parsedurl.query
        path = parsedurl.path
        data = path
        if query != "":
            data = ''.join([data, '?', query])
        data = ''.join([data, "\n"])

        if params != None:
            data = ''.join([data, params])

        hashed = hmac.new(secret_key, data, sha1)
        token = "%s:%s" % (access_key, urlsafe_b64encode(hashed.digest()))
        return token

    def CallWithForm(self, url, access_key, secret_key, params):
        headers = {}

        msg = urllib.urlencode(params)
        token = self.generate_access_token(access_key, secret_key, url, msg)

        headers['Authorization'] = 'QBox %s' % (token)
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        resp, content = httplib2.Http('').request(url, 'POST', msg, headers=headers)

        code = resp['status']
        if code != '200':
            raise Error('DigestOauthRequest.Call failed. Error was: %s %s' % (code, content))

        if len(content) != 0:
            return json.loads(content)
        return True
