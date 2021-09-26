import requests
from public.mysqldb import MySQLHelper
from urllib3 import encode_multipart_formdata
import json
import os
import re
import base64
import rsa
from urllib.parse import urlparse
import gzip
from io import BytesIO
from public.database.redis_api import RedisObj
import html
import pymysql
from pymysql.converters import escape_string
import hashlib
import chardet
from public.encryption import *
from public.publicfun import convert_interface_param, assert_fun, batch_extract_data
from InterfaceTestManage.models import *
import random

COOK = {}
UPLOAD_PATH = 'static/upload'


def unzip_data(content):
    buff = BytesIO(content)
    f = gzip.GzipFile(fileobj=buff)
    res = f.read().decode('utf-8').replace('\n', '').replace('\t', '').replace('\r', '')
    return res

# # 文件上传
# def convert_file(filed, project_id, file):
#     file = eval(file) if isinstance(file, str) else file
#     for file_item in file:
#         f = os.path.join(os.path.join(UPLOAD_PATH, str(project_id)), file_item['file_name'])
#         filed[file_item['param_name']] = (file_item['file_name'], open(f, "rb").read())
#     encode_data = encode_multipart_formdata(filed)
#     return encode_data[0], encode_data[1]
# 文件上传

def convert_file(filed, project_id, file):
    file = eval(file) if isinstance(file, str) else file
    filed = list(zip(filed.keys(), filed.values()))
    for file_item in file:
        if str(project_id) == '35':
            if file_item['param_name'] == 'file':
                f = os.path.join(os.path.join(UPLOAD_PATH, str(project_id)), file_item['file_name'])
                filed.append((file_item['param_name'], (file_item['file_name'], open(f, "rb").read())))
                encode_data = encode_multipart_formdata(filed)
            else:
                f = os.path.join(os.path.join(UPLOAD_PATH, str(project_id)), file_item['file_name'])
                param_name = "files"
                file_name = file_item['param_name']
                filed.append((param_name, (file_name, open(f, "rb").read())))
                encode_data = encode_multipart_formdata(filed)
        else:
            f = os.path.join(os.path.join(UPLOAD_PATH, str(project_id)), file_item['file_name'])
            filed.append((file_item['param_name'], (file_item['file_name'], open(f, "rb").read())))
            encode_data = encode_multipart_formdata(filed)
    return encode_data[0], encode_data[1]

# 登录加密
def check_oauth2(url):
    result = re.search(
        "/token/?$|Register",
        url)
    return result


# 登录加密
def check_login(url):
    result = re.search(
        "/login/?$|userLogin|/j_spring_security_check.action|/registerUserInfo$|/api/v1/engine/bcore/user/login|/fontLogin|/switchSubSystem|login/user$|auth/token",
        url)
    return result


# 其他接口加密
def check_other(url):
    result = re.search(
        "/login/?$|Register",
        url)
    # plan_scheduling_toBIM = "/api/v1/engine/bcore/user/login"  # 排程系统获取BIM token登录不需要加密
    # if url.find(plan_scheduling_toBIM) != -1:
    #     return 0
    return result


def interface_request(method, url, params, headers, body, file, project_id, subsystem_id, username, extract_list=[],
                      except_list=[], task_id=0, is_single_interface=False):
    '''
    :param method: 请求方法
    :param url: RUL
    :param params: 请求参数
    :param headers: 请求头
    :param body: 请求body
    :param file: 文件
    :param project_id:项目id
    :param subsystem_id: 系统id
    :param username: 操作人
    :param extract_list: 提取依赖
    :param except_list: 断言
    :param task_id: 任务id
    :param is_single_interface:是否为单一接口
    :return:
    '''
    task_id = task_id if task_id else 0
    s = requests.session()
    sql = """select cookie_param, headers, global_variable from sys_req_cookie where username='%s' and project_id=%s and 
            task_id=%s ORDER BY id desc limit 0,1""" % (username, project_id, task_id)
    #查询是否有cookie信息
    result = MySQLHelper().get_one(sql)
    # 单接口替换参数
    global_variable = json.loads(result[2]) if (result[2] if result else '') else {}
    if not task_id and is_single_interface:
        url, params, headers, body, except_list, global_variable = convert_interface_param(url, json.dumps(params), headers, body,
                                                                              except_list, global_variable, project_id)
    except_list = eval(except_list) if except_list else []
    if params and isinstance(params, dict):
        pass
    elif params and not isinstance(params, dict):
        params = json.loads(params)
    else:
        params = ''
    project_name = Sys_project.objects.get(id=project_id).project_name
    subsystem_name = Sys_subsystem.objects.get(id=subsystem_id).subsystem_name
    headers = json.loads(headers) if headers else {}
    if check_other(url):
        cookie = {}
        if project_name in ['Syrius炬星']:
            headers['Content-Type'] = "application/json"
    elif check_oauth2(url):
        cookie = {}
        clientKey = headers["clientKey"]
        clientSecret = headers["clientSecret"]
        data = clientKey + ":" + clientSecret
        Base64Encode = base64.b64encode(data.encode("utf-8")).decode()
        headers['Content-Type'] = "application/x-www-form-urlencoded"
        headers['Authorization'] = "Basic " + Base64Encode
    else:
        cookie = json.loads(result[0]) if result else {}
        if project_name in ['Syrius炬星'] and result and headers == {}: # 处理token
            Authorization = json.loads(result[1]).get('Authorization', '') if result[1] else ''
            headers['Authorization'] = "Bearer " + Authorization
            headers['Content-Type'] = "application/json"

    try:
        body = eval(body) if body else {}
    except:
        body = body.encode('utf-8') if body else {}

    # 参数形式请求
    image_file = {}
    if file:
        file_result = convert_file(body, subsystem_id, file)
        if len(file_result) != 1:
            body, header = file_result[0], file_result[1]
            headers['Content-Type'] = header
        else:
            image_file = file_result
    if isinstance(body, dict) or isinstance(body, list):
        body = json.dumps(body)
    else:
        body = body if body else ''
    if method == "POST" or method == "post":
        result = s.post(url, params=params, data=body, headers=headers, cookies=cookie, files=image_file, verify=False)
    elif method == "GET" or method == "get":
        result = s.get(url, params=params, data=body, headers=headers, cookies=cookie, files=image_file, verify=False)
    elif method == "DELETE" or method == "delete":
        result = s.delete(url, params=params, data=body, headers=headers, cookies=cookie, files=image_file, verify=False)
    elif method == "PUT" or method == "put":
        result = s.put(url, params=params, data=body, headers=headers, cookies=cookie, files=image_file, verify=False)
    elif method == "HEAD" or method == "head":
        result = s.head(url, params=params, data=body, headers=headers, cookies=cookie, files=image_file, verify=False)
    elif method == "OPTIONS" or method == "options":
        result = s.options(url, params=params, data=body, headers=headers, cookies=cookie, files=image_file, verify=False)
    elif method == "PATCH" or method == "patch":
        result = s.patch(url, params=params, data=body, headers=headers, cookies=cookie, files=image_file, verify=False)
    # 判断是否是gzip 请求头
    # if str(project_id) in ['6']:
    #     try:
    #         content = unzip_data(result.content)
    #     except:
    #         content = result.content.decode('utf-8')
    # else:
    status_code = result.status_code
    try:
        content = result.content.decode('utf-8')
        content = re.sub(r'(\\u[a-zA-Z0-9]{4})', lambda x: x.group(1).encode("utf-8").decode("unicode-escape"), content)
    except:
        content = result.text
    extract_data, except_data = '', ''
    if not task_id and is_single_interface:  # 单接口判断
        if extract_list:#提取依赖
            extract_data = batch_extract_data(extract_list, content)
            for extract in extract_data:
                extract_param_data = "extract_unit_" + extract["name"]
                global_variable[extract_param_data] = extract["result"]
        if except_list:#断言
            _, except_data = assert_fun(except_list, content, status_code)

    token_info = ''
    if (check_login(url) and (s.cookies.get_dict() is not {})) or project_name in ['Syrius炬星']:
        auth = re.findall('"data":"(.+?)"', content)
        token = re.findall('"token":"(.+?)"', content)
        userToken = re.findall('"userToken":"(.+?)"', content)
        accessToken = re.findall('"accessToken":"(.+?)"', content)
        ecdataToken = re.findall('"ecdataToken":"(.*?)"', content)
        access_token = re.findall('"access_token":"(.*?)"', content)
        auth = auth[0] if auth else ""
        token = token[0] if token else ""
        userToken = userToken[0] if userToken else ""
        accessToken = accessToken[0] if accessToken else ""
        ecdataToken = ecdataToken[0] if ecdataToken else ""
        access_token = access_token[0] if ecdataToken else ""
        if auth:
            token_info = auth
        elif token:
            token_info = token
        elif accessToken:
            token_info = accessToken
        elif userToken:
            token_info = userToken
        elif ecdataToken:
            token_info = ecdataToken
        elif access_token:
            token_info = access_token
        else:
            token_info = ""
    req_cookie_sql = "select * from sys_req_cookie where username='%s' and project_id=%s and task_id=%s ORDER BY id desc limit 1" % (
    username, project_id, task_id)
    req_cookie_info = MySQLHelper().get_one(req_cookie_sql)
    if req_cookie_info:
        if token_info:
            sql = "update sys_req_cookie set cookie_param='%s',headers='%s', global_variable='%s' where username='%s' and project_id=%s and task_id=%s" % (
                json.dumps(s.cookies.get_dict(), ), json.dumps({"Authorization": token_info}),
                escape_string(json.dumps(global_variable, ensure_ascii=False)), username, project_id, task_id)
        else:
            sql = "update sys_req_cookie set cookie_param='%s', global_variable='%s' where username='%s' and project_id=%s and task_id=%s" % (
                json.dumps(s.cookies.get_dict()), escape_string(json.dumps(global_variable, ensure_ascii=False)),
                username, project_id, task_id)
    else:
        if token_info:
            sql = "insert into sys_req_cookie(username, cookie_param, headers, task_id, project_id, global_variable) value('%s', '%s', '%s', %s, %s, '%s')" % (
                username, json.dumps(s.cookies.get_dict(), ), json.dumps({"Authorization": token_info}), task_id,
                project_id, escape_string(json.dumps(global_variable, ensure_ascii=False)))
        else:
            sql = "insert into sys_req_cookie(username, cookie_param, task_id, project_id, global_variable) value('%s', '%s', %s, %s, '%s')" % (
                username, json.dumps(s.cookies.get_dict()), task_id, project_id,
                escape_string(json.dumps(global_variable, ensure_ascii=False)))
    MySQLHelper().insert(sql)
    if isinstance(body, bytes):
        try:
            body = body.decode('utf-8')
        except:
            body = str(body)
    # body = str(body) if isinstance(body, bytes) else body
    req_param_dict = {'url': url, 'method': method, 'params': params, 'body': body, 'headers': headers,
                      'cookie': cookie,
                      'file': image_file}
    response_result = {'response_headers': dict(result.headers),
                       'response_cookie': requests.utils.dict_from_cookiejar(result.cookies)}
    return content, req_param_dict, response_result, result.status_code, global_variable, extract_data, except_data


def GetCookie():
    loginUrl = 'https://bvc-sit.bzlrobot.com/api/bvc-face/login'
    s = requests.session()
    postData = {'username': 'admin', 'password': '7501d74bbf9e67a0e7b94f47172e8e6b'}
    rs = s.post(loginUrl, postData)
    print(rs.text)
    print(s.cookies.get_dict())

    global COOK
    COOK = s.cookies.get_dict()


def DirLogin():
    s = requests.session()
    url = 'http://10.8.202.155:8080/logout'
    print(COOK)
    print(type(COOK))
    rs = s.get(url, params={'SHAREJSESSIONID': 'fde3f44a-f0fe-4a1f-a049-f0a9d5523342'})
    rs.encoding = 'utf-8'
    print(rs.text)


def request():
    file = {"file": "100006150.jpg"}
    image = []
    image_dict = {}
    for key, value in file.items():
        f = os.path.join(os.path.join(UPLOAD_PATH, "人脸"), value)
        if f.split(".")[-1].lower() in ["jpg", "png", "jpeg", "bmp"]:
            image_dict[key] = (value, open(f, "rb"))
            image.append(f)
            continue
    # url = 'http://10.8.202.155:8080/employee/uploadHead'
    # url = 'http://10.8.202.155:8080/visitor/insert'
    url = """http://10.8.202.155:8080/visitor/insert?imagePath&visitorSource=0&certificateType=0&certificateCardno=123123123123123&visitorName=自动化平台接口生成访客&visitorMobile=12345678910&visitorGroupName=广东博智林机器人有限公司&visitorGroupAddress=广东博智林机器人有限公司总部大楼&visitorGroupMobile&visitorGroupType&authorizationStatus=0&physicalCardno&sex=1&visitorType=0&companyNumbers=0&visitReasons=123&remarks&validityStartTime=2020-01-16 00:00&validityEndTime=2020-02-14 23:59&interviewees=412966497900564480&areaIdList=412966501134372864"""
    params = {}
    body = ""
    headers = {"Content-Type": "multipart/form-data"}
    cookie = {'SHAREJSESSIONID': 'b351ef46-ecba-4209-827d-376f45e21e88'}
    result = requests.session().post(url, cookies=cookie, params=params, files=image_dict, data=body, headers=headers)
    print(result.text)


if __name__ == "__main__":
    pass
    # try:
    # print(interface_request("get", "http://10.8.202.155:8080/login",{'username': 'admin', 'password':'7501d74bbf9e67a0e7b94f47172e8e6b'}, {}))
    # except BaseException as e:
    #     print(str(e))
    # GetCookie()
    # DirLogin()
    # result = requests.post(url="http://10.8.202.155:8080/organization/add", params={'SHAREJSESSIONID': '02905118-e5f8-4d8f-95ff-7420dfa6b4f1'},
    #                       data=json.dumps({"name":"新增","parentId":"","remark":"","teamLeaderId":""}),
    #                                       headers={'Content-Type': 'application/json;charset=UTF-8'})
    # result = interface_request("post", "http://10.8.202.155:8080/accessCard/insertAccessCardBatch", "{'SHAREJSESSIONID': 'bfc78a86-b7fc-4a05-b341-c2514fb7da8f'}", '{"Content-Type": "multipart/form-data"}', '', '{"file": "批量导入卡.xlsx"}', "人脸")

    # result = interface_request("post", "http://10.8.202.155:8080/employee/uploadHead", "{'SHAREJSESSIONID': '47c96aed-706e-46bc-8f15-29ee65f03502'}", '{"Content-Type": "multipart/form-data"}', '', '{"file": "批量导入卡.xlsx"}', "人脸")
    # request()
    # print(result)
    # body = AI_RAS("http://10.8.203.115:8084/opt/sys/login", json.dumps({"account": "admin", "password": "1gH7LNbe"}))
    # print(body)
    # print(requests.request(method='post',url="http://10.8.203.115:8084/opt/sys/login", data=json.dumps(body), headers={"userToken": ""}).text)
    # body = AI_RAS("http://10.8.203.115:8084/opt/sys/login", json.dumps({"account": "admin", "password": "1gH7LNbe"}))
    # print(requests.request(method='post', url="http://10.8.203.115:8084/opt/sys/login", data=body,
    #                        headers={'Content-Type': 'application/json'}).text)
