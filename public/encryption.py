# -*- coding: utf-8 -*-
# @Time    : $[DATA] $[TIME]
# @Author  : zhang lin
import json
import requests
import base64
import rsa
# from Crypto.PublicKey import RSA
# from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcsl_v1_5
from public.mysqldb import MySQLHelper
from urllib.parse import urlparse
import time
# from Crypto.Cipher import AES

class EncryPtion(object):
    def __init__(self=None):
        pass

    # 通用
    def str_RAS(self, publicKey, plaintext):
        '''
        :param publicKey: 公钥名
        :param plaintext: 需要加密的密文
        :return:
        '''
        # base64解码
        publicKeyBytes = base64.b64decode(publicKey.encode())
        # publicKeyBytes = base64.urlsafe_b64encode(publicKey)
        # 生成publicKey对象
        key = RSA.import_key(publicKeyBytes)
        if type(plaintext) == str:
            plaintext = plaintext
        else:
            try:
                if type(plaintext) == dict:
                    plaintext = json.dumps(plaintext)
            except Exception as e:
                print(e)
                return print("密文格式有误，请输入字符串或字典类型！")
        # 对原密码加密
        encryptPassword = rsa.encrypt(plaintext.encode(), key)
        return base64.b64encode(encryptPassword).decode()

    # 天眼系统
    def dict_RAS(self, key, plaintext):
        if type(plaintext) == str:
            plaintext = plaintext
        else:
            try:
                if type(plaintext) == dict:
                    plaintext = json.dumps(plaintext)
            except Exception as e:
                print(e)
                return print("密文格式有误，请输入字符串或字典类型！")
        publicKey = '''-----BEGIN PUBLIC KEY-----
        %s
        -----END PUBLIC KEY-----
        ''' % key

        a = bytes(plaintext, encoding="utf8")
        # 生成publicKey对象
        rsakey = RSA.importKey(publicKey)
        # 加密
        plaintext = Cipher_pkcsl_v1_5.new(rsakey)

        return base64.b64encode(plaintext.encrypt(a)).decode('utf-8')

# 天眼系统
def eye_rsa(body):
    if type(body) == str:
        body = json.loads(body)
    key = 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAgsmur0Xos/+KR6SexA7+7hBSsbLIeL0hVdJ/BQ6TJZqprexozkbfOkSYa7YdsUHyikKUPObdaPRbztPVT51QOjNFDG/Hoc25ljLCvpkkuCrGlQaZrRU/qgHjMJiLra4Zu5HtYyV8DdB7Kt983D51H+2c9/tCsIqXVO9I6jHqSz2yUs6x2R6+4hYTnL7fmA8lM+zPkqTWttjUYxLAv5AQigDbjyulSCm5y8r2BuN5WkAXkDuv3MwwQGxbM4NOWEdW/dwiIeqBc4Z6jQO72GotsBN17peDGHWP2UQ0KhHS8Wbl4C1jyQcX9Jl0OQrKiIgTDBhlxd28tVumvw5iZsovoQIDAQAB'
    username = EncryPtion().str_RAS(key, body["username"])
    password = EncryPtion().str_RAS(key, body["password"])
    data = json.dumps({"username": username, "password": password})
    # resule = requests.request(method="post",url=url, data=data, headers={'Content-Type': 'application/json'}).text
    return data

def encryption(method, url, key, plaintext, extract_field, encr_type=0):
    '''
    :param method: 请求方法
    :param url: pin的url地址
    :param key: 公钥名称
    :param plaintext: 明文
    :param extract_field: 识别码 uuid 或者 sn
    :param encr_type : 加密方法类型  0 = 通用   1 = FMS所用
    :return: 返回字典类型的密文和 uuid 或 sn
    '''
    # 获取公钥
    if url:
        if method == "get" or method == "GET":
            result = requests.session().get(url=url, headers={"Authorization": "Bearer"})
        elif method == "post" or method == "POST":
            result = requests.session().post(url=url, headers={"Authorization": "Bearer"})
        elif method == "put" or method == "PUT":
            result = requests.session().put(url=url, headers={"Authorization": "Bearer"})
        elif method == "delete" or method == "DELETE":
            result = requests.session().delete(url=url, headers={"Authorization": "Bearer"})
        else:
            return "请求方法错误！"
        try:
            result = json.loads(result.text)['data']
            publicKey = result.get(key, '')
        except:
            publicKey = key
    else:
        publicKey = key
    #print("publicKey:",publicKey)
    try:
        if encr_type == 0 or encr_type == '0':  # 字符串加密
            plaintext_n = EncryPtion().str_RAS(publicKey, plaintext)
        elif encr_type == 1 or encr_type == '1':  # 字典加密
            plaintext_n = EncryPtion().dict_RAS(publicKey, plaintext)
        else:
            return "请选择正确的加密方法！"
    except:
        return "加密失败"
    if extract_field == "" or extract_field == None:
        return {"get":plaintext_n}
    return {"get": plaintext_n, extract_field: result.get(extract_field, '')}

def add_to_16(par):
    par = par.encode() #先将字符串类型数据转换成字节型数据
    while len(par) % 16 != 0: #对字节型数据进行长度判断
        par += b'\x00' #如果字节型数据长度不是16倍整数就进行 补充
    return par

#海外营销活动 请求头加密
def marketing(text):
    update_time = time.strftime('%d', time.localtime(time.time()))
    password = "KiV02igi4ik3J7Q" + chr(64 + (int(update_time) % 26))
    model = AES.MODE_ECB #定义模式
    aes = AES.new(add_to_16(password),model) #创建一个aes对象
    en_text = aes.encrypt(add_to_16(text)) #加密明文
    en_text = base64.encodebytes(en_text) #将返回的字节型数据转进行base64编码
    en_text = en_text.decode('utf8') #将字节型数据转换成python中的字符串类型
    return en_text.replace('\n', '').replace('\r', '')


if __name__ == '__main__':
    pass
    # nowTime = lambda: int(round(time.time() * 1000)) # 获取当前系统时间戳，毫秒级
    # text = '{"user":"1234567@mailscode.com","activityId":"39","date":%s,"deviceId":"162642632594989363203"}' % nowTime()
    # text = '{"username":"RHSRYTJUYUKIJKH","userPhone":"23435467","email":"SDHBCDJ@qq.com","idCard":"K0987"}'
    #
    # print(marketing(text))
    # update_time = time.strftime('%d', time.localtime(time.time()))
    #     # password = "KiV02igi4ik3J7Q" + chr(64 + (int(update_time) % 26))
    #     # print(password)

# T逍客
#     url = "http://113.106.207.66:8053/api/call"
#     key = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCCmgxORkcmxF0LzGmqFVTqnX02dGFnIyDoggRY4G7bZVw3zbWsbPFAJIbzbm3hVfFm75xDu3uCda3qBiXKTeTsOXcpopypmcv3yK6YWBGuVkrZqNVNwGmk+HmLCyr5mDdlcESX2ywpCjALwljA4CfSPsiE8rouQLlAuhUAFMhszwIDAQAB"
#     username = "13631919041"
#     password = "txk@123456"
#     extract_field = ""
#     _username = encryption("POST", "", key, username, "", 1)
#     _password = encryption("POST", "", key, password, "", 1)
#     print(_username['get'])
#     print(_password['get'])
#     data = {"deviceNo":"6adf84a4de4ca3bd","loginName": _username["get"], "oprSystem":"android", "pwd": _password["get"]}
#     # print(data)
#     print(requests.session().post(url=url, params=json.dumps(data), headers={'Cookie':'TXKSID=deleteMe','nretail-tsale-api-name':'nretail.tsale.user.login'}).text)


#天眼系统
# key='MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAgsmur0Xos/+KR6SexA7+7hBSsbLIeL0hVdJ/BQ6TJZqprexozkbfOkSYa7YdsUHyikKUPObdaPRbztPVT51QOjNFDG/Hoc25ljLCvpkkuCrGlQaZrRU/qgHjMJiLra4Zu5HtYyV8DdB7Kt983D51H+2c9/tCsIqXVO9I6jHqSz2yUs6x2R6+4hYTnL7fmA8lM+zPkqTWttjUYxLAv5AQigDbjyulSCm5y8r2BuN5WkAXkDuv3MwwQGxbM4NOWEdW/dwiIeqBc4Z6jQO72GotsBN17peDGHWP2UQ0KhHS8Wbl4C1jyQcX9Jl0OQrKiIgTDBhlxd28tVumvw5iZsovoQIDAQAB'
# # username="lidongyin"
# # password="123456"
# # url = "http://data.tclo2o.cn/api/user/login"
# # _username = encryption("post", url, key, username,"")
# # _password = encryption("post", url, key, password,"")
# # data = {"username":_username["plaintext"],"password":_password["plaintext"]}
# # print(requests.session().post(url=url, data=json.dumps(data), headers={'Content-Type': 'application/json'}).text)