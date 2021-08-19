# -*- coding: utf-8 -*-
# @Time    : $[DATA] $[TIME]
# @Author  : zhang lin
import pymysql
import requests
import json


def handle_swagger_param(upload_json_data, upload_url):
    if upload_url:
        try:
            r = requests.request("GET", url=upload_url)
            if r.status_code == 200:
                return import_swagger(r.text)
            if r.status_code == 504 or r.status_code == 500 or r.status_code == 404:
                return "请求超时"
            return "失败"
        except requests.exceptions.Timeout:
            return "请求超时"
    else:
        return import_swagger(upload_json_data)


def handle_data(items, not_in_models, models_dict, params, model_key):
    value = None
    array_type = items.get('type', '')
    ref2 = items.get('$ref', '')  # items 中的关联
    if not ref2:
        if array_type in ["integer", 'number']:
            value = [0]
        elif array_type == 'string':
            value = ['string']
        elif array_type == 'object':
            value = {}
    else:
        model_name = ref2.split('/')[-1]
        try:
            value = models_dict[model_name]
            if model_name in not_in_models:
                del not_in_models[model_name]
        except:
            params['ref'] = model_name
            not_in_models.append(model_key)
    return value, not_in_models, models_dict, params


def import_swagger(json_data):
    load_dict = json.loads(json_data)
    server_name = load_dict['info']['title']
    tags_desc = load_dict['tags']
    path_info = load_dict['paths']
    models_info = load_dict['definitions']
    base_Path = load_dict['basePath']
    tags_dict = {}  # 名称
    path_list = []  # 请求路径
    models_dict = {}
    not_in_models = []

    # 处理model数据
    for model_key, model_value in models_info.items():
        params = {}
        if model_value.get("properties"):
            for p_key, p_value in model_value["properties"].items():
                value = None
                type = p_value.get('type', '')
                items = p_value.get('items', '')
                ref1 = p_value.get('$ref', '')  # properties中的关联
                if not ref1:  # 如果没有关联
                    if type in ["integer", 'number']:
                        value = 0
                    elif type == 'array':
                        value, not_in_models, models_dict, params = handle_data(items, not_in_models, models_dict,
                                                                                params,
                                                                                model_key)
                    elif type == 'string':
                        value = 'string'
                    elif type == 'object':
                        value = {}
                else:
                    model_name = ref1.split('/')[-1]
                    try:
                        value = models_dict[model_name]
                    except:
                        params['ref'] = model_name
                        not_in_models.append(model_key)
                if 'example' in p_value:
                    value = p_value['example']
                params[p_key] = value
        models_dict[model_key] = params
    # else:
    #     for model in not_in_models:
    #         result = None
    #         param = models_dict[model]
    #         for key, value in param.items():
    #             if value == None:
    #                 result = models_dict[param['ref']]
    #                 param[key] = result
    #         if param.get('ref'):
    #             del param['ref']
    #         models_dict[model] = param

    for tag in tags_desc:
        tags_dict[tag['name']] = tag['description']

    # 处理path数据
    for tags_info in tags_desc:
        for path_key, path_value in path_info.items():  # 路径信息
            for method_key, params in path_value.items():  # 请求方法
                if tags_info['name'] == params['tags'][0]:
                    tag = params['tags'][0]
                    name = server_name + "_" + tag + "_" + tags_dict[tag] + "_" + params['summary']
                    request_params = params.get("parameters", "")
                    if base_Path:
                        path = base_Path + path_key
                    else:
                        path = path_key
                    param = {}
                    body = {}
                    header = ''
                    if request_params:
                        for field_param in request_params:
                            schema = field_param.get('schema', '')
                            if schema:
                                if 'in' in field_param.keys():
                                    if field_param['in'] == 'body':
                                        sub_schema = schema.get('items')
                                        if sub_schema:
                                            model_name = sub_schema.get('$ref', '').split('/')[-1]
                                            try:
                                                body = models_dict[model_name]
                                            except:
                                                body['error'] = schema.get('$ref', '') + "not in document"
                                        else:
                                            model_name = schema.get('$ref', '').split('/')[-1]
                                            if len(schema) == 1:
                                                try:
                                                    body = models_dict[model_name]
                                                except:
                                                    body['error'] = schema.get('$ref', '') + "not in document"
                                            else:
                                                model_name = schema.get('$ref', '').split('/')[-1]
                                                if len(model_name):
                                                    try:
                                                        body = models_dict[model_name]
                                                    except:
                                                        body['error'] = schema.get('$ref', '') + "not in document"
                                                else:
                                                    field_type = schema['type']
                                                    if field_type == 'array':
                                                        if not model_name:
                                                            print(field_param)
                                                        body = [models_dict[model_name]]
                                        header = {"Content-Type": "application/json"}
                            else:
                                if field_param['in'] == 'query':
                                    try:
                                        if field_param['type'] in ['integer', 'number']:
                                            param[field_param['name']] = 0
                                        elif field_param['type'] == 'string':
                                            param[field_param['name']] = 'string'
                                    except:
                                        param = field_param['items']

                                elif field_param['in'] == 'body':
                                    if field_param['type'] in ['integer', 'number']:
                                        body[field_param['name']] = 0
                                    elif field_param['type'] == 'string':
                                        body[field_param['name']] = 'string'
                                    header = {"Content-Type": "application/json"}
                                elif field_param['in'] == 'formDate':
                                    body[field_param['name']] = 'filename'
                    header = json.dumps(header) if header else ''
                    param = json.dumps(param) if param else ''
                    body = json.dumps(body) if body else ''

                    path_list.append([name, path, method_key.upper(), header, param, body])
    # for i in path_list:
    #     print(i)
    # print(len(path_list))
    return path_list

# def conn():
#     # helper = MySQLHelper('127.0.0.1', 3306, 'root', '123456', 'auto_test')
#     helper = MySQLHelper('10.8.72.59', 3306, 'root', 'a123456', 'auto_test_xy')
#     return helper
#
#
# def insert_data(data,username,version_id,env_id):
#     count = 0
#     for i in data:
#         date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
#         is_exist = conn().get_all(
#             """select id from inte_interface where is_delete=0 and req_method='%s' and req_path='%s'""" % (i[2], i[1]))
#         if not is_exist:
#             conn().insert("""INSERT INTO inte_interface(`create_time`, `update_time`, `is_delete`, `interface_name`, `req_path`,
#             `req_method`, `req_headers`, `req_param`, `req_body`, `username`,
#              `version_id`, `env_id`,`state`) VALUES ('%s', '%s', 0, '%s', '%s', '%s', '%s','%s', '%s',
#             username, version_id, env_id,  1);""" % (date_time, date_time, i[0].strip(), i[1], i[2], i[3], i[4], i[5]))


# def import_data():
#     file_name = './钢筋-mes-20200710.json'
#     url = 'http://sit.pc.bzlrobot.com/base-api/v2/api-docs?group=cloud-base'
#     username="admin",
#     version_id = 1
#     env_id = 1
#
#     result7 = import_swagger(file_name,url)
#     insert_data(result7,username,version_id,env_id)
#
# import_data()
