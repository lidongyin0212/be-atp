# coding:utf-8
from django.shortcuts import render
from InterfaceTestManage.models import *
from public.publicfun import *
from .utils.sql_manager import *
from .utils.public_func import *

'''用户管理'''
@admin_check
def user_manager(request):
    """
    :param request: http对象
    :param scoure: 资源类型
    :return:
    """
    if request.method == "POST":
        param_list = ['activate']
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        activate = params.get('activate', '')
        user_name = params.get("user_name", '')
        online_state = params.get("online_state", 0) # 0：查询所有，1：查询离线，2：查询在线
        page = params.get('page', 1)
        rows = params.get('limit', 10)
        i = (int(page) - 1) * int(rows)
        j = (int(page) - 1) * int(rows) + int(rows)
        if activate == 1: #已激活用户
            sql = PERMISSION_LIST_LIKE % (user_name, online_state, online_state)
            user = MySQLHelper().get_all(sql)
            total = len(user)
        elif activate == 0: #待激活用户
            sql = CHECK_PERMISSION_LIST_LIKE % (user_name)
            user = MySQLHelper().get_all(sql)
            total = len(user)
        else:
            return JsonResponse({"message": "用户类型错误!", "code": 500})
        sql_params = ['id', 'username', 'username_cn', 'role', 'email', 'create_time', 'update_time', 'operator','online_state']
        resultdict = {}
        if total > 10:
            user_list = user[i:j]
        else:
            user_list = user
        data = convert_data(user_list, sql_params)
        resultdict['code'] = 0
        resultdict['msg'] = ""
        resultdict['count'] = total
        resultdict['data'] = data
        return JsonResponse(resultdict, safe=False)
    JsonResponse({"message": NOT_METHMOD, "code": 500})

#通过用户名获取用户信息
@login_check
def get_user(request):
    username = request.session.get("username", "")
    role = request.session.get("role", "")
    if request.method == "GET":
        if username:
            username_cn = Sys_user_info.objects.get(username=username, is_delete=0, state=1).username_cn
            resultdict,data = {},{}
            data['username'] = username
            data['role'] = role
            data['username_cn'] = username_cn
            resultdict['code'] = 0
            resultdict['msg'] = ""
            resultdict['data'] = data
            return JsonResponse(resultdict, safe=False)
        JsonResponse({"message": "当前用户不存在", "code": 500})
    JsonResponse({"message": NOT_METHMOD, "code": 500})

# 用户激活
@admin_check
def user_active(request, id):
    """
    :param request:  http对象
    :param id: 用户id
    :return: json数据
    """
    if request.method == "GET":
        if id:
            try:
                operator = request.session.get("username", '')
                Sys_user_info.objects.filter(id=id).update(state=1, operator=operator)
                context = {'message': ACTIVE_SUCCESS_200, 'code': 200}
                return JsonResponse(context)
            except:
                context = {'message': ACTIVE_FAIL_500, 'code': 500}
                return JsonResponse(context)
        else:
            context = {'message': ACTIVE_FAIL_500, 'code': 500}
            return JsonResponse(context)
    JsonResponse({"message": NOT_METHMOD, "code": 500})

#用户编辑
@admin_check
def user_edit(request, id):
    if request.method == 'GET':
        user_info = Sys_user_info.objects.filter(is_delete=0, id=id)
        if user_info:
            data = {'id': id, 'username': user_info[0].username, 'username_cn': user_info[0].username_cn,
                    'email': user_info[0].email, 'password': user_info[0].password}
            return JsonResponse({'message': 'ok', 'code': 200, 'data': data})
        return JsonResponse({'message': USERINFO_NOT_FIND, 'code': 500})
    elif request.method == 'POST':
        param_list = ['username_cn', 'email', 'password']
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        username_cn = params.get('username_cn', '')
        email = params.get('email', '')
        password = params.get('password', '')
        operator = request.session.get('username', '')
        user_info = Sys_user_info.objects.filter(is_delete=0, id=id)
        if user_info:
            user_info.update(username_cn=username_cn, email=email, password=password, operator=operator,
                             update_time=get_time())
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, password)
        return JsonResponse({'message': EDIT_SUCCESS_200, 'code': 200})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 用户删除
@admin_check
def user_delete(request, id):
    """
    :param request: http对象
    :param id: 用户id
    :return:
    """
    if request.method == "POST":
        per_id = Sys_user_permission.objects.filter(is_delete=0, user_id=id)
        if not per_id:
            try:
                operator = request.session.get("username", '')
                Sys_user_info.objects.filter(id=id).update(is_delete=1, operator=operator)
                context = {'message': DEL_SUCCESSS_200, 'code': 200}
                return JsonResponse(context)
            except:
                context = {'message': DEL_FAIL_500, 'code': 500}
                return JsonResponse(context)
        context = {'message': USE_MSG % ("用户", "项目"), 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})

# 权限列表
@admin_check
def permission(request, id=None, scoure=None):
    """
    :param request: http对象
    :param id: 用户id
    :param scoure: 资源类型
    :return: 树形图数据or权限列表
    """
    if request.method == "GET":
        if scoure:
            # ((1, 1, 'admin', '人脸', 1), (8, None, '123456', '', 2), (9, None, '123', '', 3))
            # 树形图
            if scoure == "user_tree": # 树形图
                user_tree = MySQLHelper().get_all(USER_PERMISSION_TREE)
                project_tree = MySQLHelper().get_all(PROJECT_PERMISSION_TREE)
                user_data, project_data = handle_tree_data(user_tree), handle_tree_data(project_tree)
                return JsonResponse({'user_data': user_data, 'project_data': project_data})
            elif scoure == "user_permission_list": #按用户授权列表
                user_name = request.GET.get("user_name", '')
                sql = USER_PERMISSION_TREE % user_name
                result = MySQLHelper().get_all(sql)
                data, count = handle_user_list(request, result)
                resultdict = {}
                resultdict['code'] = 0
                resultdict['msg'] = ""
                resultdict['count'] = count
                resultdict['data'] = data
                return JsonResponse(resultdict)
            elif scoure == "project_permission_list": # 按项目授权列表
                project_name = request.GET.get("project_name", '')
                sql = PROJECT_PERMISSION_TREE % project_name
                result = MySQLHelper().get_all(sql)
                data, count = handle_project_list(request, result)
                resultdict = {}
                resultdict['code'] = 0
                resultdict['msg'] = ""
                resultdict['count'] = count
                resultdict['data'] = data
                return JsonResponse(resultdict, safe=False)
            elif scoure == "project": #编辑权限获取项目列表
                result = handle_user_data(id)
                return JsonResponse({'not_permission': result[0], 'permission': result[1], 'code':0})
            elif scoure == "user": #编辑权限获取用户列表
                result = handle_project_data(id)
                return JsonResponse({'not_permission': result[0], 'permission': result[1], 'code':0})
            else:
                return JsonResponse({'message': "URL路径错误!", 'code': 500})
        return JsonResponse({'message': "scoure不存在", 'code': 500})
    elif request.method == "POST": # 添加与删除权限
        try:
            params = eval(request.body)
            data_list = params.get("data", "")
            operate = params.get("operate", "")
            username = request.session['username']
            type = params.get("type", "")
            #操作授权
            if type == "user":
                # for project_id in data_list:
                if operate == "add":
                    for project_id in data_list:
                        result = Sys_user_permission.objects.filter(user_id=id, project_id=project_id)
                        if len(result) == 0:
                            Sys_user_permission.objects.create(user_id=id, project_id=project_id, username=username)
                        else:
                            result.update(is_delete=0)
                    return JsonResponse({'message': "授权成功", 'code': 200})
                elif operate == "del":
                    for project_id in data_list:
                        Sys_user_permission.objects.filter(user_id=id, project_id=project_id).update(is_delete=1)
                    return JsonResponse({'message': "取消成功", 'code': 200})
                else:
                    return JsonResponse({'message': "operate参数错误！", 'code': 500})
            elif type == "project":
                # for user_id in data_list:
                if operate == "add":
                    for user_id in data_list:
                        result = Sys_user_permission.objects.filter(user_id=user_id, project_id=id)
                        if len(result) == 0:
                            Sys_user_permission.objects.create(user_id=user_id, project_id=id, username=username)
                        else:
                            result.update(is_delete=0)
                    return JsonResponse({'message': "授权成功", 'code': 200})
                elif operate == "del":
                    for user_id in data_list:
                        Sys_user_permission.objects.filter(user_id=user_id, project_id=id).update(is_delete=1)
                    return JsonResponse({'message': "取消成功", 'code': 200})
                else:
                    return JsonResponse({'message': "operate参数错误！", 'code': 500})
            else:
                return JsonResponse({'message': "type参数错误！", 'code': 500})
        except:
            return JsonResponse({'message': PERMISSION_FAIL_500, 'code': 500})
    context = {'message': DEL_FAIL_500, 'code': 500}
    return JsonResponse(context)


# ((1, 1, 'admin', '人脸', 1), (8, None, '123456', '', 2), (9, None, '123', '', 3))
# 处理用户权限数据
def handle_user_list(request, permission_data,):
    """
    :param request: http对象
    :param permission_data: 查询到的数据库原始数据
    :return:
    """
    page = request.GET.get('page', 1)
    rows = request.GET.get('limit', 10)
    i = (int(page) - 1) * int(rows)
    j = (int(page) - 1) * int(rows) + int(rows)
    data = {}
    for user in permission_data:
        sub_data = {}
        if str(user[0]) not in data:
            sub_data["user_id"] = str(user[0])
            sub_data["username_cn"] = user[2]
            sub_data["project_name"] = user[3]
            sub_data["role"] = user[4]
            sub_data["username"] = user[5]
            data[str(user[0])] = sub_data
        else:
            if user[3] and data[str(user[0])]["project_name"]:
                data[str(user[0])]["project_name"] = data[str(user[0])]["project_name"] + "， " + user[3]
            elif user[3] and not data[str(user[0])]["project_name"]:
                data[str(user[0])]["project_name"] = user[3]
    user_data = []
    for value in data.values():
        user_data.append(value)
    count = len(user_data)
    if count > 10:
        return user_data[i:j], count
    return user_data, count


# 按项目获取权限列表
def handle_project_list(request, permission_data,):
    """
    :param request: http对象
    :param permission_data: 查询到的数据库原始数据
    :return:
    """
    page = request.GET.get('page', 1)
    rows = request.GET.get('limit', 10)
    i = (int(page) - 1) * int(rows)
    j = (int(page) - 1) * int(rows) + int(rows)
    data = {}
    for user in permission_data:
        sub_data = {}
        if str(user[0]) not in data:
            sub_data["project_id"] = str(user[0])
            sub_data["project_name"] = user[2]
            sub_data["user_list"] = user[3]
            data[str(user[0])] = sub_data
        else:
            if user[3] and data[str(user[0])]["user_list"]:
                data[str(user[0])]["user_list"] = data[str(user[0])]["user_list"] + "， " + user[3]
            elif user[3] and not data[str(user[0])]["user_list"]:
                data[str(user[0])]["user_list"] = user[3]
    user_data = []
    for value in data.values():
        user_data.append(value)
    count = len(user_data)
    if count > 10:
        return user_data[i:j], count
    return user_data, count


# 穿梭框使用
# 处理项目权限数据
def handle_project_data(id):
    """
    :param id: 项目id
    :return: 按项目id划分权限
    """
    not_permission_sql = "select id , project_name from sys_project where is_delete='0'"
    permission_sql = "select project_id from sys_user_permission where is_delete='0' and user_id=%s"
    not_permission_result = MySQLHelper().get_all(not_permission_sql)
    permission_result = MySQLHelper().get_all(permission_sql, (id,))
    project_list = []
    for project_id in permission_result:
        project_list.append(str(project_id[0]))
    params = ['value', 'title']
    return convert_data(not_permission_result, params), project_list


# 穿梭框使用
# 处理用户权限数据
def handle_user_data(id):
    """
    :param id: 用户id
    :return: 按用户id划分权限
    """
    not_permission_sql = "select id , username_cn from sys_user_info where is_delete=0 and state=1"
    permission_sql = "select user_id from sys_user_permission where is_delete='0' and project_id=%s"
    not_permission_result = MySQLHelper().get_all(not_permission_sql)
    permission_result = MySQLHelper().get_all(permission_sql, (id,))
    user_list = []
    for project_id in permission_result:
        user_list.append(str(project_id[0]))
    params = ['value', 'title']
    return convert_data(not_permission_result, params), user_list


# 穿梭框权限操作
@admin_check
def permission_delete(request, id):
    """
    :param request: http对象
    :param id: 用户id或者项目id
    :return: 操作结果
    """
    if request.method == "POST":
        params = eval(request.body)
        type = params.get("type", "")
        try:
            if type == "user":
                Sys_user_permission.objects.filter(user_id=id).update(is_delete=1)
            else:
                Sys_user_permission.objects.filter(project_id=id).update(is_delete=1)
            context = {'message': DEL_SUCCESSS_200, 'code': 200}
            return JsonResponse(context)
        except:
            context = {'message': DEL_FAIL_500, 'code': 500}
            return JsonResponse(context)
    JsonResponse({"message": NOT_METHMOD, "code": 500})

