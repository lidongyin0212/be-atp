import re
from InterfaceTestManage.models import Sys_public_param, Sys_user_info, Sys_data_driven, Sys_encryption, \
    Inte_task_record, Sys_dict, Inte_task
import json
from public.database.mysql_api import *
from public.database.redis_api import *
from public.database.mongodb_api import *
from constant import SQL_OPERATE_FAIL_500, SQL_OPERATE_SUCCESS_200, DATA_NO_FOUND
import datetime
from .generator import *
from InterfaceTestManage.utils.sql_manager import SELECT_INTERFACE_EXTRACT_LIST2, SELECT_INTERFACE_EXTRACT_LIST
from django.http import HttpResponseRedirect, JsonResponse
from constant import *
from public.encryption import *
from InterfaceTestManage.utils.sql_manager import *
from public.mysqldb import MySQLHelper
import demjson
import unittest


def get_time():
    return time.strftime(
        '%Y-%m-%d %H:%M:%S', time.localtime(time.time()))


# 权限校验
def permission_check(func):
    def wrapper(request, *args, **kwargs):
        username = request.session.get('username')
        param_list = ['project_id']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({"message": param, "code": 0})
        project_id = param.get('project_id', '')
        if type(project_id) == list:
            for id in project_id:
                id = int(id)
                result = MySQLHelper().get_all(PROJECT_PERMISSION_CHEKE, (username, id))
                if not result:
                    return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        else:
            id = int(project_id)
            result = MySQLHelper().get_all(PROJECT_PERMISSION_CHEKE, (username, id))
            if not result:
                return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        try:
            ret = func(request, *args, **kwargs)
        except Exception as e:
            if 'positional argument' in str(e):
                return JsonResponse({"message": "URL缺失参数", "code": 500})
            return JsonResponse({"message": str(e), "code": 500})
        return ret

    return wrapper


# 用户登录
def operate_check(func):
    def wrapper(request, *args, **kwargs):
        username = request.session.get('username')
        ret = func(request, *args, **kwargs)
        return ret

    return wrapper

# 用户登录
def login_check(func):
    def wrapper(request, *args, **kwargs):
        username = request.session.get('username')
        if not username:
            if request.is_ajax():
                return JsonResponse({"message": "还未登陆, 请重新登陆", "code": 401, "timestamp": get_time()})
            else:
                return JsonResponse({"message": "session会话过期!", "code": 405})
                # return HttpResponseRedirect('/login')
        Sys_user_info.objects.filter(username=request.session.get('username')).update(update_time=get_time())
        try:
            ret = func(request, *args, **kwargs)
        except Exception as e:
            if 'positional argument' in str(e):
                return JsonResponse({"message": "URL缺失参数", "code": 500})
            return JsonResponse({"message": str(e), "code": 500})
        return ret
    return wrapper


# 管理员权限
def admin_check(func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('username'):
            if request.is_ajax():
                return JsonResponse({"message": "还未登陆, 请重新登陆", "code": 401, "timestamp": get_time()})
            else:
                return JsonResponse({"message": "session会话过期!", "code": 405})
        userinfo = Sys_user_info.objects.filter(username=request.session.get('username'))
        if userinfo[0] and userinfo[0].role != 1:
            context = {'message': NOT_PERMISSION, 'code': 500}
            return JsonResponse(context)
        userinfo.update(update_time=get_time())
        try:
            ret = func(request, *args, **kwargs)
        except Exception as e:
            if 'positional argument' in str(e):
                return JsonResponse({"message": "URL缺失参数", "code": 500})
            return JsonResponse({"message": str(e), "code": 500})
        return ret

    return wrapper


def extract_data(extract_rule, result_data):
    '''
    :param extract_rule: 提取字段
    :param result_data: 实际结果
    :return:
    '''
    resp_str = re.findall(r'"%s":"(.*?)"' % extract_rule, result_data, re.S)
    resp_int = re.findall(r'"%s":(\d+)' % extract_rule, result_data, re.S)
    _resp_str = re.findall(r'"%s": "(.*?)"' % extract_rule, result_data, re.S)
    _resp_int = re.findall(r'"%s": (\d+)' % extract_rule, result_data, re.S)
    if resp_str and resp_int:
        return resp_str + resp_int
    elif _resp_str and _resp_int:
        return _resp_str  + _resp_int
    elif _resp_int:
        return _resp_int
    elif _resp_str:
        return _resp_str
    elif resp_str:
        return resp_str
    elif resp_int:
        return resp_int
    else:
        rest_json = demjson.decode(result_data)[extract_rule]
        if rest_json:
            if type(rest_json) == bool:
                rest_json = str(rest_json)
                return [rest_json]
            return rest_json
        else: # 匹配不到，手动写正则
            resp_data = re.findall(extract_rule, result_data, re.S)
            return resp_data


def batch_extract_data(extract_rule_list, result_data):
    '''
    :param extract_rule_list: 依赖规则
    :param result_data: 响应结果数据
    :return:
    '''
    extract_result = []
    if isinstance(extract_rule_list, str):
        extract_rule_list = eval(extract_rule_list)
    for extract_rule in extract_rule_list:
        result = {}
        result["name"] = extract_rule["name"]
        result["rule"] = extract_rule["rule"]
        result["result"] = extract_data(extract_rule["rule"], result_data)
        extract_result.append(result)
    return extract_result


# 变量应用
def convert_params(params, DEPEND_DATA, project_id=0):
    result_arr = re.findall(r'\{\{\w+\}\}\[\d+\]\[\\".+?\\"\]|\{\{\w+\}\}\[\d+\]\[".+?"\]|\{\{\w+\}\}\[\\".+?\\"\]|'
                            r'\{\{\w+\}\}\[".+?"\]|\{\{\w+\}\}\[\d+\]|\{\{\w+\}\}',
                            params)
    if result_arr:
        for result in result_arr:
            # TODO 自定义变量
            param_unit = re.match(r"^\{\{(.*?)\}\}$", result)
            if param_unit:
                try:
                    # 自增变量替换
                    param_unit_data = "custom_unit_" + param_unit.group(1)
                    if param_unit_data not in DEPEND_DATA:
                        custom_data = convert_customparam(param_unit.group(1), project_id)
                        DEPEND_DATA[param_unit_data] = custom_data
                        params = params.replace(result, custom_data)
                    else:
                        params = params.replace(result, DEPEND_DATA[param_unit_data])
                except Exception as e:
                    print(e)
                    # 提取变量列表
                    if param_unit_data in DEPEND_DATA:
                        params = params.replace(result, str(DEPEND_DATA[param_unit_data]))
                    else:
                        raise KeyError("自定义变量:%s，值为空" % param_unit.group(1))
            # TODO 依赖变量
            extract_unit = re.match(r'^\{\{(\w+)\}\}\[(\d+)\]$', result)
            if extract_unit:  # 数据依赖
                extract_name, index = extract_unit.group(1), extract_unit.group(2)
                extract_param_data = "extract_unit_" + extract_name
                if extract_name:
                    try:
                        params = params.replace(result, str(DEPEND_DATA[extract_param_data][int(index)]))
                    except Exception as e:
                        print(e)
                        raise KeyError("提取变量:%s，值为空" % extract_name)
                else:
                    raise KeyError("提取变量:%s，值为空" % extract_name)
            # TODO 加密签名
            encrypty_param1 = re.match(r'^\{\{(\w+)\}\}\[\\"(.+?)\\"\]$', result)
            encrypty_param2 = re.match(r'^\{\{(\w+)\}\}\["(.+?)"\]$', result)
            if encrypty_param1 or encrypty_param2:  # 加密数据
                encrypty_param = encrypty_param1 if encrypty_param1 else encrypty_param2
                encrypty_name, field_name = encrypty_param.group(1), encrypty_param.group(2)
                try:
                    encrypty_param_data = "encrypty_unit_" + encrypty_name
                    encrypty_list = Sys_encryption.objects.filter(variable_name=encrypty_name,
                                                                  is_delete=0,project_id=int(project_id))[0]


                    encrypty_data = encryption(encrypty_list.request_method, encrypty_list.url,
                                               encrypty_list.publickey, encrypty_list.plaintext,
                                               encrypty_list.extract_field, str(encrypty_list.encr_type))
                    DEPEND_DATA[encrypty_param_data] = encrypty_data
                    params = params.replace(result, str(encrypty_data[field_name]))
                except Exception as e:
                    print(e)
                    if encrypty_param_data in DEPEND_DATA:
                        params = params.replace(result, str(DEPEND_DATA[encrypty_param_data][field_name]))
                    else:
                        raise KeyError("加密变量:%s，值为空" % encrypty_data)
            # TODO 数据库驱动
            sql_unit1 = re.match(r'^\{\{(\w+)\}\}\[(\d+)\]\[\\"(.+?)\\"\]$', result)
            sql_unit2 = re.match(r'^\{\{(\w+)\}\}\[(\d+)\]\["(.+?)"\]$', result)
            if sql_unit1 or sql_unit2: # 数据库变量
                sql_unit = sql_unit1 if sql_unit1 else sql_unit2
                sql_name, index, field_name = sql_unit.group(1), sql_unit.group(2), sql_unit.group(3)
                sql_data = check_type(sql_name, project_id)
                if sql_data:
                    sql_param_data = json.loads(sql_data)
                    try:
                        params = params.replace(result, str(sql_param_data[int(index)][field_name]))
                    except Exception as e:
                        print(e)
                        raise KeyError("数据库变量:%s，值为空" % sql_name)
                else:
                    raise KeyError("数据库变量:%s，值为空" % sql_name)
    return params, DEPEND_DATA


# 转化数据驱动数据
def convert_dataDriven(params):
    data_list = []
    param_unit = re.findall(r'\{\w\}\[".+?"\]', params["req_param"])
    body_unit = re.findall(r'\{\w\}\[".+?"\]', params["req_body"])
    if param_unit:
        dataDriven_match = re.search(r'\$\{(.*?)\}\["(.+?)"\]', param_unit[0])
        dataDriven_data = Sys_data_driven.objects.filter(param_name=dataDriven_match.group(1))[0].param_list
        for ddt_data in eval(dataDriven_data):
            params_bak = params.copy()
            for result in param_unit:
                data_param = re.search(r'\$\{(.*?)\}\["(.+?)"\]', result)
                params_bak["req_param"] = params_bak["req_param"].replace(
                    result, ddt_data[data_param.group(2)])
            data_list.append(params_bak)
    elif body_unit:
        dataDriven_match = re.search(r'\$\{(.*?)\}\["(.+?)"\]', body_unit[0])
        dataDriven_data = Sys_data_driven.objects.filter(param_name=dataDriven_match.group(1))[0].param_list
        for ddt_data in dataDriven_data:
            params_bak = params.copy()
            for result in body_unit:
                data_param = re.search(r'\$\{(.*?)\}\["(.+?)"\]', result)
                params_bak["req_body"] = params_bak["req_body"].replace(result, ddt_data[data_param.group(2)])
            data_list.append(params_bak)
    else:
        data_list.append(params)
    return data_list


def check_type(param_name, project_id=0):
    # param_info = Public_Param.objects.get(param_name=param_name, is_delete=0)
    # # obj = MySQLObj(host="127.0.0.1", port=3306, user='root', password='123456', db='interface_v04')
    # # param_info = obj.get_one("select `type` from public_param where param_name=%s", (param_name))
    # if param_info:
    #     if param_info.type == 3:
    sql = """select sys_db_env.db_type, sys_db_env.env_ip, sys_db_env.env_port, sys_db_env.`user`, sys_db_env.`password`, 
            sys_db_env.dbname, `sql` from sys_db_env 
            left join sys_db_sqldetail on sys_db_env.id=sys_db_sqldetail.env_id 
            where sys_db_env.is_delete=0 and sys_db_sqldetail.is_delete=0 and sql_name='%s' and project_id = %s
            """ % (param_name, project_id)
    result_data = MySQLHelper().get_one(sql)
    if result_data:
        result, message, ret = database_query(type=result_data[0], host=result_data[1], port=int(result_data[2]),
                                              user=result_data[3], password=result_data[4],
                                              db=result_data[5], sql=result_data[6])
        return result
    return None


# 数据库查询可视化数据
def convert_chart_data(ret, params):
    data_dict = {}
    count = 0
    for field in params:
        data_list = []
        for item in ret:
            data_list.append(item[count])
        count += 1
        data_dict[field] = data_list
    return data_dict


# 数据库查询时转换数据
def convert_data(ret, params, flag=False):
    data_list = []
    for info in ret:
        count = 0
        data_dict = {}
        for item1 in info:
            if item1 is None:
                item1 = ''
            if params[count] in ["except_list", 'extract_list', 'req_file', 'req_param',
                                 'step_list'] and item1 and flag:
                try:
                    item1 = eval(item1)
                except:
                    item1 = json.loads(item1)
            data_dict[params[count]] = item1
            count += 1
        data_list.append(data_dict)
    return data_list


# 数据库查询时转换数据
def convert_ui_data(ret, params):
    data_list = []
    for info in ret:
        count = 0
        data_dict = {}
        for item1 in info:
            if params[count] in ["step_list"]:
                item1 = eval(item1)
                data_dict['count'] = len(item1)
            data_dict[params[count]] = item1
            count += 1
        data_list.append(data_dict)
    return data_list


# 一对多数据转换 用于规则提取字段
def convert_one_to_many_data(ret, params, flag=False):
    field = ['id', 'name', 'rule', 'dataFormat'] if flag else ['name', 'rule', 'dataFormat']
    sql = SELECT_INTERFACE_EXTRACT_LIST if flag else SELECT_INTERFACE_EXTRACT_LIST2
    data_list = []
    for info in ret:
        count = 0
        data_dict = {}
        for item1 in info:
            if item1 is None:
                item1 = ''
            if params[count] == "extract_list" and item1:
                extract_list = str(item1) if item1 else ''
                sql1 = sql % "(" + extract_list + ")"
                result = MySQLHelper().get_all(sql1)
                item1 = convert_data(result, field, True)
            if params[count] in ["except_list", 'req_file', 'req_param'] and item1 and flag:
                item1 = eval(item1)
            data_dict[params[count]] = item1
            count += 1
        data_list.append(data_dict)
    return data_list


def assert_fun(scoure_rule, result):
    '''
    :param scoure_rule: 预期结果
    :param result: 实际结果
    :return:
    '''
    # 1 断言失败 2 执行成功
    scoure_rule = eval(scoure_rule) if isinstance(scoure_rule, str) else scoure_rule
    assert_ret = []
    # result = result.decode(encoding="utf-8")
    for sub_rule in scoure_rule:
        assertType = sub_rule.get("assert_name", '')
        extract_result, except_result = extract_assert_data(sub_rule, result)
        if assertType == "assertEqual": # 等于
            try:
                if str(except_result) == str(extract_result):
                    sub_rule['result'] = 2
                    assert_ret.append(sub_rule)
                else:
                    sub_rule['result'] = 1
                    assert_ret.append(sub_rule)
                    return 1, assert_ret
            except Exception as e:
                return 1, str(sub_rule) + ',%s' % e
        elif assertType == "assertNotEqual": # 不等于
            try:
                if str(except_result) != str(extract_result):
                    sub_rule['result'] = 2
                    assert_ret.append(sub_rule)
                else:
                    sub_rule['result'] = 1
                    assert_ret.append(sub_rule)
                    return 1, assert_ret
            except Exception as e:
                return 1, str(sub_rule) + ',%s' % e
        elif assertType == "assertIn": # 包括
            try:
                if str(except_result) in str(extract_result):
                    sub_rule['result'] = 2
                    assert_ret.append(sub_rule)
                else:
                    sub_rule['result'] = 1
                    assert_ret.append(sub_rule)
                    return 1, assert_ret
            except Exception as e:
                return 1, str(sub_rule) + ',%s' % e
        elif assertType == "assertNotIn": # 不包括
            try:
                if str(except_result) not in str(extract_result):
                    sub_rule['result'] = 2
                    assert_ret.append(sub_rule)
                else:
                    sub_rule['result'] = 1
                    assert_ret.append(sub_rule)
                    return 1, assert_ret
            except Exception as e:
                return 1, str(sub_rule) + ',%s' % e
        else:
            pass
    return 2, assert_ret


# 断言提取
def extract_assert_data(scoure_rule, result):
    '''
    :param scoure_rule: 断言规则
    :param result: 实际结果
    :return:
    '''
    except_result, extract_rule,site = scoure_rule.get("except_result", ''), \
                                             scoure_rule.get("assert_rule", '').replace("\\\\", "\\"), \
                                             scoure_rule.get("site", '')

    extract_result = extract_data(extract_rule, result)
    site = (int(site) - 1) if site else 0
    state = 1 if extract_result else 0
    if site and ((site + 1) > len(extract_result)):
        return extract_result[0], except_result
    if state == 0:
        return extract_result, except_result
    return extract_result[site], except_result

def task_record(task_id, ret):
    """
    :param task_id: 任务id
    :param ret: 执行结果 0 执行失败 1 断言失败 2 执行成功
    :return:
    """
    record_info = Inte_task_record.objects.filter(task_id=task_id, create_time__gte=datetime.datetime.now().date())
    if record_info:
        execute_count = record_info[0].execute_count
        if ret == 0:
            fail_count = record_info[0].fail_count
            record_info.update(execute_count=execute_count + 1, fail_count=fail_count + 1)
        elif ret == 1:
            assert_count = record_info[0].assert_count
            print(type(assert_count))
            record_info.update(execute_count=execute_count + 1, assert_count=assert_count + 1)
        elif ret == 2:
            success_count = record_info[0].success_count
            record_info.update(execute_count=execute_count + 1, success_count=success_count + 1)
    else:
        record_info = Inte_task_record.objects
        if ret == 0:
            record_info.create(task_id=task_id, execute_count=1, fail_count=1)
        elif ret == 1:
            record_info.create(task_id=task_id, execute_count=1, asset_accout=1)
        elif ret == 2:
            record_info.create(task_id=task_id, execute_count=1, success_count=1)


def convert_to_json(data):
    if data:
        try:
            if isinstance(data, dict) or isinstance(data, list):
                data = json.dumps(data, ensure_ascii=False)
            else:
                data = json.dumps(json.loads(data), ensure_ascii=False)
        except:
            pass
    return data


# 数据库操作
def database_query(type, host, port, user, password, sql, db=None):
    mysql_fields, redis_fields, mongodb_fields, message = None, None, None, ""
    if type == 1:
        result, mysql_fields, message = mysql_operate(host=host, port=int(port), user=user, password=password, db=db,
                                                      sql=sql)
    elif type == 2:
        result, redis_fields, message = redis_operate(host=host, port=int(port), password=password, sql=sql)
    elif type == 3:
        result, mongodb_fields, message = mongodb_operate(host=host, port=int(port), user=user, password=password,
                                                          db=db, sql=sql)
    data = []
    if mysql_fields is not None:  # 关系型数据结构才使用
        for row in result:
            ret, i = {}, 0
            for col in mysql_fields:
                value = row[i]
                if isinstance(value, datetime.datetime):
                    ret[col] = value.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    ret[col] = str(row[i])
                i += 1
            data.append(ret)
        return json.dumps(data), message, 0

    if redis_fields is not None:
        data_dict = {}
        data_dict[redis_fields] = result
        data.append(data_dict)
    if mongodb_fields is not None:
        data = list(result)
    if result != -1:
        return json.dumps(data, cls=CJsonEncoder), message, 0
    return json.dumps(data, cls=CJsonEncoder), message, -1


# 转化成多次执行数据
def convert_runtime(data):
    data_list = []
    for D in data:
        if D['run_time'] != '1':
            for i in range(0, D['run_time']):
                data_list.append(D)
        else:
            data_list.append(D)
    return data_list


# 转化单接口参数
def convert_interface_param(url, params, headers, body, except_list, DEPEND_DATA, project_id):
    url, DEPEND_DATA = convert_params(url, DEPEND_DATA, project_id)
    if params:
        params, DEPEND_DATA = convert_params(params, DEPEND_DATA, project_id)
    if headers:
        headers, DEPEND_DATA = convert_params(headers, DEPEND_DATA, project_id)
    if body:
        body, DEPEND_DATA = convert_params(body, DEPEND_DATA, project_id)
    if except_list:
        except_list, DEPEND_DATA = convert_params(str(except_list), DEPEND_DATA, project_id)
    return url, params, headers, body, except_list, DEPEND_DATA

def convert_customparam(data, project_id=0):
    sql = """select `sys_public_param`.id, param_name, rule, `sys_dict`.dict_key, input_params from `sys_public_param`
            left join `sys_dict` on `sys_public_param`.rule = `sys_dict`.id where `sys_public_param`.is_delete=0
            and param_type = 2 and param_name = '%s' and project_id= %s """ % (data, project_id,)
    param_list = MySQLHelper().get_all(sql)
    # param_list = MySQLHelper().get_all(
    #     """select `sys_public_param`.id, param_name, rule, `sys_dict`.dict_key, input_params from `sys_public_param`
    #         left join `sys_dict` on `sys_public_param`.rule = `sys_dict`.id
    #         where `sys_public_param`.is_delete=0 and param_type = 2 and param_name = %s""",
    #     (data,))

    sql_params = [
        'id', 'param_name', 'rule', 'dict_key', 'input_params'
    ]
    rule_data = convert_data(param_list, sql_params)
    input_param = rule_data[0]['input_params'] if rule_data[0]['input_params'] else ''
    input_param = tuple(input_param.split(','))
    if rule_data[0]['dict_key'] == 'factory_generate_ids':
        param_result = eval(rule_data[0]['dict_key'])(rule_data[0]['id'], input_param)
    else:
        param_result = eval(rule_data[0]['dict_key'])(input_param)
    return param_result


def convert_customparam_test(rule, input_params):
    input_param = input_params if input_params else ''
    input_param = tuple(input_param.split(','))
    param_dict = Sys_dict.objects.filter(id=rule)
    if param_dict:
        dict_key = param_dict[0].dict_key
        if dict_key == 'factory_generate_ids':
            param_result = eval('factory_generate_ids_test')(input_param)
        else:
            param_result = eval(dict_key)(input_param)
        return param_result


def mysql_operate(host, port, user, password, db, sql):
    ret, field = -1, None
    obj = MySQLObj(host=host, port=int(port), user=user, password=password, db=db)
    operate = sql.split()[0].lower()
    if operate == "select":
        ret, field, message = obj.get_all(sql)
    elif operate == "insert":
        ret, message = obj.insert(sql)
    elif operate == "update":
        ret, message = obj.update(sql)
    elif operate == "delete":
        ret, message = obj.delete(sql)
    else:
        ret, message = -1, operate
    if ret != -1:
        return ret, field, SQL_OPERATE_SUCCESS_200 % operate
    return ret, field, SQL_OPERATE_FAIL_500 % (operate, str(message))


def redis_operate(host, port, password, sql):
    message = ''
    obj = RedisObj(host=host, port=int(port), password=password)
    operate = sql.split()[0].lower()
    key = sql.replace(operate + ' ', '')
    if operate == "get":
        ret = obj.get_data(key.strip())
        if not ret:
            message = DATA_NO_FOUND % key
        else:
            message = SQL_OPERATE_SUCCESS_200 % operate
    return ret, key, message


def mongodb_operate(host, port, user, password, db, sql):
    message = ''
    find_result = re.findall('getCollection\("(.+?)"\)\.(.+?)\((.+?)\)', sql)
    if not find_result:
        return None, '', 'sql语句格式错误'
    db_operate_str = 'mongo.' + find_result[0][1] + '("' + find_result[0][0] + '",' + find_result[0][2] + ')'
    with MongoObj(host, int(port), db, user, password) as mongo:
        result = eval(db_operate_str)
    if result:
        return result, '', SQL_OPERATE_SUCCESS_200 % find_result[0][1]
    else:
        return result, '', DATA_NO_FOUND % find_result[0][2]


def params_secrect(param, param_list):
    for item in param_list:
        if item not in param.keys():
            msg = "缺失参数：%s" % item
            return 0, msg
        if isinstance(param[item], str) and param[item].strip() == "":
            msg = "参数：%s 不能为'%s'" % (item, param[item])
            return 0, msg
        if param[item] == None:
            msg = "参数：%s 不能为null" % item
            return 0, msg
    return 1, ''


def params_check(body, param_list):
    try:
        if body:
            param = json.loads(body)
        else:
            param = {}
    except:
        # msg = "The parameter is not valid JSON format"
        msg = "该参数不是有效的JSON格式"
        return 0, msg
    if param_list:
        param_ret, msg = params_secrect(param, param_list)
        if not param_ret:
            return 0, msg
    return 1, param


def handle_ui_case_data(case_data):
    data = []
    for user in case_data:
        sub_data = {}
        sub_data["title"] = user[1]
        sub_data["id"] = user[0]
        sub_data["level"] = '1'
        # 判断用例是否为前置用例或者后置用例
        data.append(sub_data)
    return data


# json 数据中包含
class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)



if __name__ == "__main__":
    pass
    # print(convert_params('{"parentId": {{1}}, "page": "1", "limit": "10"}', {"1": "simple_data", "2": 111111}))
    # print(convert_params("""/organization/delete/{{org_id}}[0]""", {"org_id":[10]}))
    # print(convert_params("""{"RobotTypeVersion":{"id":"","version":"新增机器人类型版本007","description":"007",
    # "unitText":"12","robotTypeId":{{robot_type_id}}[0],"managerId":{{user_id}}[0]}}""", {"user_id": ["114"]}))
