# coding:utf-8
import json
import traceback
import openpyxl
import tempfile
import threading
import socket
from django.shortcuts import render
from public.interface_request import interface_request
from InterfaceTestManage.utils import loghelper
from public.TestRun import Test
from public.publicfun import *
from public.generator import *
from .utils.public_func import *
from apscheduler.schedulers.background import BackgroundScheduler
from bulk_update.helper import bulk_update
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from apscheduler.triggers.cron import CronTrigger
from public.copy_function import *
from public.export_function import *
from public.thread_manage import *
from public.mysqldb import MySQLHelper
# from public.task import SCHEDULER
from django.http import HttpResponse
from public.task import *
from public.importSQL import *
from InterfaceTestManage.utils.user_operate import user_operate
from InterfaceAutoTest.settings import *
loghelper = loghelper.loghelper()
logger = loghelper.get_logger()

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 47200))
except socket.error:
    print("!!!scheduler already started, DO NOTHING")


# 登录
def login(request):
    if request.method == "POST":
        param_list = ['username', 'password']
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        # post发送请求，就是表单里面的请求进来了
        username = params.get('username', '').strip()
        password = params.get('password', '').strip()
        if len(username) > 30 or len(password) > 20:
            return JsonResponse({'message': INPUT_LONG, 'code': 500})

        if not Sys_user_info.objects.filter(username=username, is_delete=0):
            return JsonResponse({'message': "T信账号不存在", 'code': 500})
        if Sys_user_info.objects.filter(username=username, is_delete=0, state=0):
            return JsonResponse({'message': "T信账号未激活", 'code': 500})
        user = Sys_user_info.objects
        user_info = user.filter(username=username, password=password, state=1, is_delete=0)
        role = user.get(username=username, is_delete=0).role
        count = user_info.count()

        if count:
            # 登录成功，如果存在用户名和密码
            request.session['username'] = username
            request.session['password'] = password
            request.session['role'] = role
            remeberPw = params.get('remeberPw', '')
            redirect_index = HttpResponseRedirect('/index')
            if remeberPw:
                redirect_index.set_cookie('username', username)
                redirect_index.set_cookie('password', password)
                redirect_index.set_cookie('role', role)
            user_info.update(update_time=get_time())
            name_cn = user.get(username=username, is_delete=0).username_cn
            object_desc = name_cn + "(" + username + ")"
            user_operate(username, "be_login", "ob_user_info", object_desc)  # 用户操作记录日志
            return JsonResponse({'message': '登录成功', 'code': 200})
            # return  request.getRequestDispatcher().forward('/index')

        else:
            print('用户名或密码错误')
            context = {'message': '用户名或密码错误', 'code': 500}
            logger.info('用户名:{username}和密码:{password}存在错误啊！ '.format(
                username=username, password=password))
            loghelper.close_handler()
            return JsonResponse(context)
    JsonResponse({"message": NOT_METHMOD, "code": 500})

# 新开的登出
@login_check
def logout_new(request):
    if request.method == 'GET':
        try:
            print(request.session['username'])
            username = request.session.get("username", "")
            if username:
                del request.session['username']
                return JsonResponse({"message": "登出成功", "code": 200})
        except KeyError:
            print(KeyError)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 注册
def register(request):
    if request.method == 'POST':
        param_list = ['username', 'username_cn', 'email', 'password']
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        username = params.get('username', '')
        username_cn = params.get('username_cn', '')
        email = params.get('email', '')
        password = params.get('password', '')
        type = params.get("type", "")  # 管理员注册用户
        operator = request.session.get('username', '')
        user_info = Sys_user_info.objects
        #长度校验
        if len(username) > 30 or len(username_cn) > 10 or len(email) > 50 or len(password) > 20:
            return JsonResponse({'message': INPUT_LONG, 'code': 500})
        # 将数据进行注册
        # 后台对获取的数据进行校验,之后在传递.
        if (username is not None and len(username) <= 20 and username_cn is not None and len(
                username_cn) <= 20 and password is not None
                and len(password) <= 16):
            if user_info.filter(username=username, is_delete=0):
                context = {"message": "账号已存在", 'code': 500}
                return JsonResponse(context)
            try:
                if type:
                    operator_role = Sys_user_info.objects.filter(username=operator, is_delete=0)[0].role

                    if operator_role == 1:
                        user_info.create(username=username, username_cn=username_cn, password=password, email=email,
                                         role=2,
                                         state=1,
                                         operator=operator)
                        context = {"message": "添加成功！", 'code': 200}
                        user_operate(username, "be_enroll", "ob_user_info", username)  # 用户操作记录日志
                    else:
                        context = {"message": "添加出现其他问题", 'code': 500}
                else:
                    id = user_info.create(username=username, username_cn=username_cn, password=password, email=email,
                                          role=2).id
                    context = {"message": "注册成功, 请联系管理员激活！", 'code': 200}
                    user_operate(username, "be_enroll", "ob_user_info", username)  # 用户操作记录日志
                return JsonResponse(context)
            except Exception as e:
                context = {"message": "注册出现其他问题", 'code': 500}
            return JsonResponse(context)
        return JsonResponse({"message": "用户名或者密码不符合要求", "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 修改密码
@login_check
def edit_passwd(request):
    if request.method == "POST":
        username = request.session.get('username', '')
        state, param = params_check(request.body, ["old_pwd", "new_pwd"])
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        old_pwd = param.get('old_pwd', '')
        new_pwd = param.get('new_pwd', '')
        if len(old_pwd) > 20:
            return JsonResponse({"code": 500, "message": "旧密码超长"})
        if len(new_pwd) > 20:
            return JsonResponse({"code": 500, "message": "新密码超长"})
        if old_pwd == new_pwd:
            return JsonResponse({"code": 500, "message": "旧密码与新密相同"})

        result = Sys_user_info.objects.filter(username=username, password=old_pwd, is_delete=0, state=1)
        if result:
            result.update(password=new_pwd)
            object_desc = "旧密码:" + old_pwd + "，新密码:" + new_pwd
            # object_id = json.dumps({"old_pwd":old_pwd,"new_pwd":new_pwd})
            user_operate(username, "be_edit_pwd", "ob_user_info", object_desc)  # 用户操作记录日志
            try:
                del request.session['username']
            except KeyError:
                print(KeyError)
                return JsonResponse({"message": "session会话过期!", "code": 405})
            return JsonResponse({"message": EDIT_SUCCESS_200, "code": 200})
        return JsonResponse({"code": 500, "message": "旧密码不正确"})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})

# 首页项目数据
@login_check
def index_all_data(request):
    if request.method == "POST":
        username = request.session.get('username', '')
        sql_params = [
            'project_count', 'interface_count', 'case_count', 'task_count', 'tasking_count'
        ]
        msg, code = "ok", 200
        sql = PROJECT_DATA % username
        result = MySQLHelper().get_all(sql)
        try:
            data = convert_data(result, sql_params)[0]
        except Exception as e:
            print(e)
            data = {}
            msg = SERVER_ERROR
            code = 500
        result_dict = {"message": msg, "code": code, "data": data}
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 首页指定项目数据
@login_check
def index_data(request, project_id=0):
    if request.method == "POST":
        username = request.session.get("username", "")
        param_list = ['type']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        type = param.get("type", "")
        if type == 'bar': # 柱状图数据
            if not int(project_id):
                sql = BAR_DATA_PROJECT % username
                result = MySQLHelper().get_all(sql)
            else:
                sql = BAR_DATA_SUBSYSTEM % (username, project_id)
                result = MySQLHelper().get_all(sql)
            sql_params = ['id', 'project_name', 'interface_count', 'case_count']
        elif type == 'line': # 折线图数据
            day = param.get("day", "")
            result = MySQLHelper().get_all(LINE_DATA, (int(day) - 1, username, project_id, project_id))
            sql_params = ['datetime', 'count', 'success_count', 'assert_count', 'fail_count']
        msg, code = "ok", 200
        try:
            data = convert_chart_data(result, sql_params)  # 数据库查询可视化数据
        except Exception as e:
            print(e)
            data = {}
            msg = SERVER_ERROR  # "服务器错误"
            code = 500
        result_dict = {"message": msg, "code": code, "data": data}
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})  # NOT_METHMOD=无该请求方式


# 项目列表
@login_check
def project_root(request):
    if request.method == "POST":
        username = request.session.get("username", "")
        sql_params = ['id', 'project_name']
        msg, code = "ok", 200
        try:
            data = convert_data(MySQLHelper().get_all(ENV_PROJECT_LIST, (username,)), sql_params)
        except Exception as e:
            print(e)
            msg = SERVER_ERROR
            data = []
        result_dict = {"message": msg, "code": code, "data": data}
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 项目管理列表
@login_check
def project_manager(request):
    username = request.session.get('username', '')
    if request.method == "GET":
        role = Sys_user_info.objects.filter(username=username)[0].role
        # return render(request, 'project/project-list.html', {"role": role})
    elif request.method == "POST":
        param_list, result_dict, msg = [], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        page = param.get("page", '')
        limit = param.get("limit", '')
        project_name = param.get("project_name", "")
        # 检验参数
        sql = PROJECT_LIST_LIKE % (username, project_name)
        project_list = MySQLHelper().get_all(sql)
        if page and limit:
            i = (int(page) - 1) * int(limit)
            j = (int(page) - 1) * int(limit) + int(limit)
            sub_project = project_list[i:j]
        else:
            sub_project = project_list
        total = len(project_list)
        sql_params = ['id', 'project_name', 'project_desc']
        try:
            data = convert_data(sub_project, sql_params)
        except Exception as e:
            print(e)
            msg = SERVER_ERROR
            data = []
        result_dict['code'] = 0
        result_dict['msg'] = msg if msg else ""
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 项目新增
@admin_check
def project_add(request):
    if request.method == 'POST':
        param_list = ['project_name']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        project_name = param.get("project_name", "")
        project_desc = param.get("project_desc", "")
        username = request.session.get("username", '')
        project_info = Sys_project.objects
        project_exist = Sys_project.objects.filter(project_name=project_name, is_delete=0)
        if len(project_name) > 18:
            return JsonResponse({"message": "项目名称超长", "code": 500})
        if project_exist:
            context = {"message": NAME_REPETITION, "code": 500}
            return JsonResponse(context)
        if project_name:
            project_id = project_info.create(
                project_name=project_name,
                project_desc=project_desc,
                username=username).id
            user_list = list(Sys_user_info.objects.filter(role=1).values_list('id', flat=True))
            for i in user_list:
                Sys_user_permission.objects.create(
                    project_id=project_id, username=username, user_id=i)
            context = {"message": ADD_SUCCESS_200, "code": 200}
            object_desc = project_name + '(' + str(project_id) + ')'
            user_operate(username, "be_add", "ob_project", object_desc)  # 用户操作记录日志
        else:
            context = {"message": ADD_FAIL_500, "code": 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 项目编辑
@admin_check
def project_edit(request, id):
    username = request.session.get('username', '')
    # 根据项目id关联权限表
    project_permission = MySQLHelper().get_all(PROJECT_PERMISSION_CHEKE, (username, id))
    if not project_permission:
        return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
    if request.method == 'GET':
        project_obj = Sys_project.objects
        project_info = project_obj.get(id=id)
        data = {'id': id, 'project_name': project_info.project_name, 'project_desc': project_info.project_desc}
        return JsonResponse({'message': 'ok', 'code': 200, 'data': data})
    elif request.method == 'POST':
        param_list = ['project_name']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        project_name = param.get("project_name", "")
        project_desc = param.get("project_desc", "")
        if len(project_name) > 18:
            return JsonResponse({"message": "项目名称超长", "code": 500})
        if int(id):
            project_obj = Sys_project.objects
            project_exist = project_obj.filter(project_name=project_name, is_delete=0).exclude(id=id)
            if project_exist:
                context = {"message": NAME_REPETITION, "code": 500}
                return JsonResponse(context)
            project_info = project_obj.filter(id=id)
            try:
                project_info.update(
                    project_name=project_name,
                    project_desc=project_desc,
                    username=username,
                    update_time=get_time())
                context = {'message': EDIT_SUCCESS_200, 'code': 200}
                object_desc = project_name + '(' + str(id) + ')'
                user_operate(username, "be_edit", "ob_project", object_desc)  # 用户操作记录日志
            except Exception as e:
                print(e)
                context = {'message': EDIT_FAIL_500, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 项目删除
@admin_check
def project_delete(request):
    username = request.session.get("username", "")
    role = Sys_user_info.objects.filter(username=username, is_delete=0)[0].role
    if role != 1:
        return JsonResponse({"message": NOT_PERMISSION, "code": 500})
    if request.method == "POST":
        # 批量删除
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get("ids")
        del_ids = []
        if type(ids) == list:
            for id in ids:
                sub_sys = Sys_subsystem.objects.filter(project_id=id, is_delete=0)
                if sub_sys:
                    return JsonResponse({"message": "与子系统有关联，删除失败！", "code": 500})
                Sys_project.objects.filter(id=id, is_delete=0).update(is_delete=1, username=username)
                Sys_user_permission.objects.filter(project_id=id).update(is_delete=1, username=username)
                del_ids.append(id)
            if len(del_ids) == len(ids):
                context = {"message": DEL_SUCCESSS_200, "code": 200}
                id = ",".join(map(str, ids))
                project_name = Sys_project.objects.get(id=int(id)).project_name
                object_desc = project_name + '(' + str(id) + ')'
                user_operate(username, "be_del", "ob_project", object_desc)  # 用户操作记录日志
            else:
                context = {"message": DEL_FAIL_500, "code": 500}
            return JsonResponse(context)
        return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 环境管理列表
@login_check
def environment_manager(request):
    username = request.session.get("username", "")
    if request.method == "GET":
        pass
        # return render(request, 'env/environ-list.html')
    elif request.method == "POST":
        param_list, result_dict, msg = [], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        page = param.get("page", 1)
        limit = param.get("limit", 10)
        subsystem_id = param.get("subsystem_id", '')
        env_name = param.get("env_name", "")
        project_id = param.get("project_id", "")
        sql = ENV_LIST_LIKE % (username, env_name, subsystem_id, subsystem_id, project_id, project_id)
        env_list = MySQLHelper().get_all(sql)
        total = len(env_list)
        if total > 10:
            i = (int(page) - 1) * int(limit)
            j = (int(page) - 1) * int(limit) + int(limit)
            sub_env = env_list[i:j]
        else:
            sub_env = env_list
        sql_params = [
            "id", "project_id", "project_name", "env_name", "host", "port",
            "env_desc", "username", "update_time","creator"
        ]
        try:
            data = convert_data(sub_env, sql_params)
        except Exception as e:
            print(e)
            msg = SERVER_ERROR
            data = []
        result_dict['code'] = 0
        result_dict['msg'] = msg if msg else ""
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 环境下拉框列表
@login_check
def env_list(request, id):
    username = request.session.get('username', '')
    if request.method == "GET":
        data = convert_data(MySQLHelper().get_all(PROJECT_ENV_LIST, (id, username)),
                            ['id', 'env_name'])
        return JsonResponse({"message": 'ok', "code": 200, 'data': data})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 判断环境是否存在
@login_check
def env_exist(request, id):
    if request.method == "POST":
        env_id = Sys_module.objects.filter(id=id)[0].env_id
        if env_id:
            return JsonResponse({"message": 'env exist', "code": 200})
        return JsonResponse({"message": 'env not exist', "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 获取任务用例环境
@login_check
def get_env(request):
    if request.method == "GET":
        type = request.GET.get('type', '')
        task_id = request.GET.get('task_id', '')
        id = request.GET.get('id', '')
        if not task_id:
            return JsonResponse({"message": NOT_PARAM, "code": 500})
        subsystem_case_dict = Inte_task.objects.filter(id=task_id, is_delete=0)
        if not subsystem_case_dict:
            return JsonResponse({"message": TASK_NOT_FOUND, "code": 500})
        if not subsystem_case_dict[0].case_dict:
            return JsonResponse({"message": TASK_IS_EMPTY, "code": 500})
        if type == "subsystem":
            subsystem_case_list = eval(subsystem_case_dict[0].case_dict).get(str(id), '')
            if not subsystem_case_list:
                return JsonResponse({"message": SUBSYSTEM_NOT_CASE, "code": 500})
            task_case_id = subsystem_case_list.split(',')[0]
            env_id = Inte_task_case.objects.filter(case_id=task_case_id, task_id=task_id, is_delete=0)[0].env_id
            return JsonResponse({"message": 'ok', 'data': {"env_id": env_id}, "code": 200})
        elif type == "module":
            module_list = Sys_module.objects.filter(id=id, is_delete=0)
            if module_list:
                case_list = module_list[0].case_list
                if not case_list:
                    return JsonResponse({"message": MODULE_NOT_CASE, "code": 500})
                subsystem_id = module_list[0].subsystem_id
                subsystem_case_list = eval(subsystem_case_dict[0].case_dict).get(str(subsystem_id), '')
                if not subsystem_case_list:
                    return JsonResponse({"message": SUBSYSTEM_NOT_CASE, "code": 500})
                case_id = ''
                for x in case_list.split(','):
                    if x in subsystem_case_list.split(','):
                        case_id = x
                        break
                if not case_id:
                    return JsonResponse({"message": MODULE_NOT_CASE, "code": 500})
                env_id = Inte_task_case.objects.filter(case_id=case_id, task_id=task_id, is_delete=0)[0].env_id
                return JsonResponse({"message": 'ok', 'data': {"env_id": env_id}, "code": 200})
            return JsonResponse({"message": MODULE_NOT_CASE, "code": 500})
        elif type == "case":
            case_info = Inte_task_case.objects.filter(case_id=id, task_id=task_id, is_delete=0)
            if not case_info:
                return JsonResponse({"message": CASE_NOT_ENV, 'data': {"env_id": ""},"code": 200})
            env_id = case_info[0].env_id
            return JsonResponse({"message": 'ok', 'data': {"env_id": env_id}, "code": 200})
        else:
            return JsonResponse({"message": NOT_PARAM, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})

#编辑任务用例环境
@login_check
def save_env(request):
    if request.method == 'POST':
        param_list, result_dict, msg = ['type', 'task_id', 'id', 'env_id'], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        operate_type = param.get('type', '')
        id = param.get('id', '')
        task_id = param.get('task_id', '')
        env_id = param.get('env_id', '')
        task_list = Inte_task.objects.filter(id=task_id, is_delete=0)
        if not task_list:
            return JsonResponse({"message": TASK_NOT_FOUND, "code": 500})
        case_dict = task_list[0].case_dict
        if not case_dict:
            return JsonResponse({"message": TASK_IS_EMPTY, "code": 500})
        if operate_type == "subsystem":
            case_list = eval(case_dict).get(str(id), '')
            if not case_list:
                return JsonResponse({"message": SUBSYSTEM_NOT_CASE, "code": 500})
            Inte_task_case.objects.filter(case_id__in=case_list.split(','), is_delete=0, task_id=task_id).update(
                env_id=env_id)
        elif operate_type == "module":
            module_list = Sys_module.objects.filter(id=id, is_delete=0)
            if not module_list:
                return JsonResponse({"message": MODULE_NOT_FOUND, "code": 500})
            case_list = module_list[0].case_list
            if not case_list:
                return JsonResponse({"message": MODULE_NOT_CASE, "code": 500})
            subsystem_id = module_list[0].subsystem_id
            task_case_list = eval(case_dict).get(str(subsystem_id), '')
            if not task_case_list:
                return JsonResponse({"message": SUBSYSTEM_NOT_CASE, "code": 500})
            exist_task_case = [x for x in case_list.split(',') if x in task_case_list.split(',')]
            Inte_task_case.objects.filter(case_id__in=exist_task_case, is_delete=0, task_id=task_id).update(
                env_id=env_id)
        elif operate_type == "case":
            Inte_task_case.objects.filter(case_id=id, is_delete=0, task_id=task_id).update(
                env_id=env_id)
        else:
            return JsonResponse({"message": NOT_PARAM, "code": 500})
        return JsonResponse({"message": EDIT_SUCCESS_200, "code": 200})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 环境新增
@login_check
def environment_add(request):
    if request.method == 'POST':
        param_list, result_dict, msg = ['project_id', 'subsystem_id', 'env_name', 'host'], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})

        project_id = param.get('project_id', '')
        subsystem_id = param.get('subsystem_id', '')
        env_name = param.get('env_name', '').strip()
        host = param.get('host', '').strip()
        port = param.get('port', '').strip()
        env_desc = param.get('env_desc', '').strip()
        username = request.session.get("username", '')
        environment = Sys_env.objects
        if len(env_name) > 50:
            return JsonResponse({"message": "环境名称超长", "code": 500})
        if environment.filter(env_name=env_name, subsystem_id=subsystem_id, is_delete=0):
            return JsonResponse({'message': NAME_REPETITION, 'code': 500})
        project_permission = MySQLHelper().get_all(GET_PERSON_PROJECT, (username, project_id))
        if len(project_permission):
            id = environment.create(
                env_name=env_name,
                host=host,
                port=port,
                env_desc=env_desc,
                username=username,
                project_id=project_id,
                subsystem_id=subsystem_id,
                creator=username).id
            object_desc = env_name + '(' + str(id) + ')'
            user_operate(username, "be_add", "ob_env", object_desc)  # 用户操作记录日志
            context = {'message': ADD_SUCCESS_200, 'code': 200}
        else:
            context = {'message': NOT_PERMISSION, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 环境编辑
@login_check
def environment_edit(request, id):
    username = request.session.get("username", "")
    result = MySQLHelper().get_all(ENV_OPERATE, (username, id))
    if not result:
        return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
    if request.method == 'GET':
        env_result = MySQLHelper().get_all(GET_ONE_ENV, (username, id))
        env_info = convert_data(env_result,
                                ['id', 'env_name', 'project_id', 'project_name', 'subsystem_name',
                                 'host', 'port',
                                 'env_desc'])
        return JsonResponse({'message': 'ok', 'code': 200, 'data': env_info[0] if env_info else []})
    elif request.method == 'POST':
        param_list, result_dict, msg = ['env_name', 'host', 'project_id'], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        env_name = param.get('env_name', '')
        host = param.get('host', '')
        port = param.get('port', '')
        env_desc = param.get('env_desc', '')
        project_id = param.get('project_id', '')
        if len(env_name) > 50:
            return JsonResponse({"message": "环境名称超长", "code": 500})
        if int(id):
            if Sys_env.objects.filter(env_name=env_name, project_id=project_id, is_delete=0).exclude(id=id):
                return JsonResponse({'message': NAME_REPETITION, 'code': 500})
            environ_info = Sys_env.objects.filter(id=id, is_delete=0)
            update_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                        time.localtime(time.time()))
            try:
                environ_info.update(
                    env_name=env_name,
                    host=host,
                    port=port,
                    env_desc=env_desc,
                    update_time=update_time,
                    username=username)
                context = {'message': EDIT_SUCCESS_200, 'code': 200}
                object_desc = env_name + '(' + str(id) + ')'
                user_operate(username, "be_edit", "ob_env", object_desc)  # 用户操作记录日志
            except Exception as e:
                print(e)
                context = {'message': EDIT_FAIL_500, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 环境删除
@login_check
def environment_delete(request):
    username = request.session.get("username", "")
    if request.method == "POST":
        # 删除所有
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get("ids")
        map_ids = map(str, ids)  # 格式化
        str_ids = ",".join(map_ids)  # 转换成 str 类型
        # 根据环境id关联权限表
        sql = DELETE_ENV_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        env_name, del_ids = [], []
        if type(ids) == list:
            for id in ids:
                if Sys_module.objects.filter(env_id=id, is_delete=0, module_type=1):
                    return JsonResponse({'message': "删除失败，与模块有关联", 'code': 500})
                if Inte_interface.objects.filter(env_id=id, is_delete=0):
                    return JsonResponse({'message': "删除失败，与接口有关联", 'code': 500})
                if Sys_module.objects.filter(env_id=id, is_delete=0, module_type=1):
                    return JsonResponse({'message': "删除失败，与用例有关联", 'code': 500})
            for id in ids:
                    Sys_env.objects.filter(id=id).update(is_delete=1, username=username)
                    del_ids.append(id)
                    env_name.append(Sys_env.objects.get(id=id).env_name)
            if len(ids) == len(del_ids):
                context = {'message': DEL_SUCCESSS_200, 'code': 200}
                object_desc = ",".join(map(str, env_name)) + '(' + str_ids + ')'
                user_operate(username, "be_del", "ob_env", object_desc)  # 用户操作记录日志
            else:
                context = {'message': USING_MSG % "环境", 'code': 500}
            return JsonResponse(context)
        return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 修改接口状态
@login_check
def change_state(request, scoure=None):
    username = request.session.get("username", "")
    if request.method == "POST":
        param_list, result_dict, msg = ['id', 'state'], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        # type = param.get('type', '')
        id = param.get('id', '')
        state = param.get('state', '')
        # 根据接口id关联权限表
        # project_permission = MySQLHelper().get_all(CHEKE_API_PERMISSION, (username, id))
        # if not project_permission:
        #   return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        behavior = "be_enabled" if state == 1 else "be_disable"
        if scoure == 'interface':
            Inte_interface.objects.filter(is_delete=0, id=id).update(state=state, update_time=get_time(),
                                                                     username=username)
            case_list = Inte_case.objects.filter(is_delete=0, interface_id=id)
            case_list.update(state=state, update_time=get_time(), username=username)
            case_id = list(case_list.values_list('id', flat=True))
            Inte_task_case.objects.filter(is_delete=0, case_id__in=case_id).update(state=state, update_time=get_time(),
                                                                                   username=username)
            interface_name = Inte_interface.objects.get(id=id).interface_name
            object_desc = interface_name + '(' + str(id) + ')'
            user_operate(username, behavior, "ob_interface", object_desc)  # 用户操作记录日志
        elif scoure == 'case_interface':
            case_list = Inte_case.objects.filter(is_delete=0, id=id)
            case_list.update(state=state, update_time=get_time(), username=username)
            case_id = list(case_list.values_list('id', flat=True))
            Inte_task_case.objects.filter(is_delete=0, case_id__in=case_id).update(state=state, update_time=get_time(),
                                                                                   username=username)
            if int(state) ==1:
                interface_id = Inte_case.objects.get(is_delete=0,id=int(id)).interface_id
                Inte_interface.objects.filter(id=interface_id, is_delete=0).update(state=state, update_time=get_time(),
                                                                                   username=username)
            case_name = Inte_case.objects.get(id=id).case_name
            object_desc = case_name + '(' + str(id) + ')'
            user_operate(username, behavior, "ob_case", object_desc)  # 用户操作记录日志
        elif scoure == 'task_case':
            Inte_task_case.objects.filter(is_delete=0, id=id).update(state=state, update_time=get_time(),
                                                                     username=username)
            task_case_name = Inte_task_case.objects.get(id=id).case_name
            object_desc = task_case_name + '(' + str(id) + ')'
            user_operate(username, behavior, "ob_task_case", object_desc)  # 用户操作记录日志
        else:
            return JsonResponse({"message": NOT_TYPE, "code": 500})
        return JsonResponse({'message': EDIT_SUCCESS_200, 'code': 200})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 接口管理列表
@login_check
def interface_manager(request):
    if request.method == "GET":
        pass
        # return render(request, 'interface/interface-list.html')
    elif request.method == "POST":
        param_list, result_dict, msg = ['subsystem_id'], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 0})
        page = param.get("page", 1)
        limit = param.get("limit", 10)
        interface_name = param.get("interface_name", "")
        subsystem_id = param.get("subsystem_id", "")
        state_choose = param.get("state", 2)
        username = request.session.get("username")
        sql = INTERFACE_LIST_LIKE % (username, interface_name, subsystem_id, state_choose, state_choose)
        interface_list = MySQLHelper().get_all(sql)
        i = (int(page) - 1) * int(limit)
        j = (int(page) - 1) * int(limit) + int(limit)
        total = len(interface_list)
        if total > 10:
            sub_interface = interface_list[i:j]
        else:
            sub_interface = interface_list
        sql_params = [
            'id', 'interface_name', 'req_path', 'req_method',
            'state', 'username', 'update_time', 'case_count','creator']
        try:
            data = convert_data(sub_interface, sql_params, True)
        except Exception as e:
            print(e)
            msg = SERVER_ERROR
            data = []
        result_dict['code'] = 0
        result_dict['msg'] = msg if msg else ""
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 指定版本的接口列表下拉框
@login_check
def interface_list(request):
    if request.method == "POST":
        param_list, result_dict, msg = ['subsystem_id'], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        subsystem_id = param.get("subsystem_id", "")
        username = request.session.get("username")
        sql = INTERFACE_LIST % (username, subsystem_id)
        interface_list = MySQLHelper().get_all(sql)
        total = len(interface_list)
        sql_params = ['id', 'interface_name', 'url', 'state']
        try:
            data = convert_data(interface_list, sql_params)
        except Exception as e:
            print(e)
            msg = SERVER_ERROR
            data = []
        result_dict['code'] = 0
        result_dict['msg'] = msg if msg else ""
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 接口新增
@login_check
def interface_add(request):
    if request.method == 'POST':
        param_list, result_dict, msg = ['interface_name', 'req_path', 'req_method', 'subsystem_id',
                                        'env_id', ], {}, 'ok'
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        interface_name = params.get('interface_name', '')
        req_path = params.get('req_path', '')
        req_method = params.get('req_method', '')
        req_headers = params.get('req_headers', '')
        req_param = convert_to_json(params.get('req_param')) if params.get('req_param', '') else ''
        req_file = json.dumps(params.get('req_file'), ensure_ascii=False) if params.get('req_file', '') else ''
        req_body = convert_to_json(params.get('req_body')) if params.get('req_body', '') else ''
        except_list = json.dumps(params.get('except_list'), ensure_ascii=False) if params.get('except_list', '') else ''
        extract_list = json.dumps(params.get('extract_list'), ensure_ascii=False) if params.get('extract_list',
                                                                                                '') else ''
        subsystem_id = params.get('subsystem_id', '')
        env_id = params.get('env_id', '')
        username = request.session.get("username", '')
        project_id = Sys_subsystem.objects.get(id=subsystem_id, is_delete=0).project_id
        project_permission = MySQLHelper().get_all(GET_PERSON_VERSION, (username, subsystem_id))
        if len(project_permission):
            interface = Inte_interface.objects
            interface_name_exist = interface.filter(interface_name=interface_name, subsystem_id=subsystem_id,
                                                    is_delete=0)
            if interface_name_exist:
                context = {'message': INTERFACE_NAME_EXIST, 'code': 500}
                return JsonResponse(context)
            if len(interface_name) > 0 and len(req_path) and len(req_method):
                id = interface.create(
                    interface_name=interface_name,
                    req_path=req_path,
                    req_method=req_method,
                    req_headers=req_headers,
                    req_param=req_param,
                    req_body=req_body,
                    req_file=req_file,
                    username=username,
                    except_list=except_list,
                    extract_list=extract_list,
                    subsystem_id=subsystem_id,
                    env_id=env_id,
                    creator=username,
                    project_id=project_id).id
                context = {'message': ADD_SUCCESS_200, 'code': 200}
                object_desc = interface_name + '(' + str(id) + ')'
                user_operate(username, "be_add", "ob_interface", object_desc)  # 用户操作记录日志
            else:
                context = {'message': ADD_FAIL_500, 'code': 500}
        else:
            context = {'message': NOT_PERMISSION, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 接口编辑
@login_check
def interface_edit(request, id):
    if request.method == 'GET':
        username = request.session.get('username', '')
        interface_param = [
            'id', 'interface_name', 'req_path', 'req_method', 'req_headers',
            'req_param', 'req_body', 'req_file', 'extract_list', 'except_list', 'project_id', 'project_name',
            'subsystem_id', 'subsystem_name', 'env_id'
        ]
        ret = MySQLHelper().get_all(SELECT_INTERFACE_INFO, (username, id))
        interface_info = convert_data(ret, interface_param, True)
        data = interface_info if interface_info else []
        return JsonResponse({'message': 'ok', 'code': 200, 'data': data})
    elif request.method == 'POST':
        param_list, result_dict, msg = ['interface_name', 'req_path', 'req_method', 'subsystem_id',
                                        'env_id', ], {}, 'ok'
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        subsystem_id = params.get('subsystem_id', '').strip()
        env_id = params.get('env_id', '')
        interface_name = params.get('interface_name', '')
        req_path = params.get('req_path', '')
        req_method = params.get('req_method', '')
        req_headers = params.get('req_headers', '')
        req_param = convert_to_json(params.get('req_param')) if params.get('req_param', '') else ''
        req_file = json.dumps(params.get('req_file'), ensure_ascii=False) if params.get('req_file', '') else ''
        req_body = convert_to_json(params.get('req_body')) if params.get('req_body', '') else ''
        except_list = json.dumps(params.get('except_list'), ensure_ascii=False) if params.get('except_list', '') else ''
        extract_list = params.get('extract_list', '')
        username = request.session.get("username", '')
        project_permission = MySQLHelper().get_all(GET_PERSON_VERSION, (username, subsystem_id))
        project_id = Sys_subsystem.objects.get(id=subsystem_id, is_delete=0).project_id
        if project_permission:
            if int(id):
                interface_obj = Inte_interface.objects
                interface_name_exist = interface_obj.filter(interface_name=interface_name, subsystem_id=subsystem_id,
                                                            is_delete=0).exclude(id=id)
                if interface_name_exist:
                    context = {'message': INTERFACE_NAME_EXIST, 'code': 500}
                    return JsonResponse(context)
                interface_info = interface_obj.filter(id=id, is_delete=0)
                update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                try:
                    interface_info.update(
                        interface_name=interface_name,
                        req_path=req_path,
                        req_method=req_method,
                        req_headers=req_headers,
                        subsystem_id=subsystem_id,
                        env_id=env_id,
                        req_param=req_param,
                        username=username,
                        except_list=except_list,
                        extract_list=extract_list,
                        update_time=update_time,
                        req_body=req_body,
                        req_file=req_file,
                        project_id=project_id)
                    old_time = time.time()
                    case_list = Inte_case.objects.filter(interface_id=id, is_delete=0)
                    case_list.update(req_path=req_path, req_method=req_method, req_headers=req_headers)
                    Inte_task_case.objects.filter(case_id__in=list(case_list.values_list('id', flat=True))).update(
                        req_path=req_path, req_method=req_method, req_headers=req_headers)
                    print(time.time() - old_time)
                    context = {'message': EDIT_SUCCESS_200, 'code': 200}
                    object_desc = interface_name + '(' + str(id) + ')'
                    old_time = time.time()
                    user_operate(username, "be_edit", "ob_interface", object_desc)  # 用户操作记录日志
                    print(time.time() - old_time)
                except Exception as e:
                    print(e)
                    context = {'message': EDIT_FAIL_500, 'code': 500}
        else:
            context = {'message': NOT_PERMISSION, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 接口删除
@login_check
def interface_delete(request):
    username = request.session.get("username", "")
    if request.method == "POST":
        # 删除所有
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get("ids")
        map_ids = map(str, ids)  # 格式化
        str_ids = ",".join(map_ids)  # 转换成 str 类型
        sql = DELETE_API_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        del_ids = []
        if type(ids) == list:
            for id in ids:
                if Inte_case.objects.filter(interface_id=id, is_delete=0):
                    continue
                else:
                    Inte_interface.objects.filter(id=id, is_delete=0).update(is_delete=1, username=username)
                    del_ids.append(id)
            if len(ids) == len(del_ids):
                user_operate(username, "be_del", "ob_interface", str_ids)  # 用户操作记录日志
                return JsonResponse({'message': DEL_SUCCESSS_200, 'code': 200})
            else:
                if len(del_ids) < 1:
                    return JsonResponse({'message': "接口与用例有关联，删除失败", 'code': 500})
                return JsonResponse({'message': "成功删除%s条" % len(del_ids), 'code': 200})
        return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 用例管理列表
@login_check
def case_manager(request, scoure=None):
    username = request.session.get("username", "")
    if request.method == "GET":
        pass
        # return render(request, 'interface/case-list.html')
    elif request.method == "POST":
        param_list, result_dict, msg = ['subsystem_id'], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        subsystem_id = param.get("subsystem_id", "")
        if scoure != "tree":  # 用例列表
            page = param.get("page", 1)
            limit = param.get("limit", 10)
            detail = param.get('detail', '')
            module_id = param.get('module_id', '')
            state_choose = param.get('state', 2)
            type_choose = param.get('case_type', '')
            if module_id:  # 指定模块的用例列表
                case_if_list = Sys_module.objects.get(id=module_id).case_list
                # case_if_list = get_case_list(module_id) + ',' + case_if_list
                case_if_list = case_if_list.strip(',') if case_if_list else ''
                if type_choose:
                    sql = SELECT_CASE_LIST % (username, state_choose, state_choose, type_choose, case_if_list, case_if_list)
                else:
                    sql = SELECT_CASE_LIST_NOTYPE % (username, state_choose, state_choose, case_if_list, case_if_list)
                case_interface_list = MySQLHelper().get_all(sql) if case_if_list else []
            else:
                # # 必填参数
                # state, msg = params_secrect(param, ['subsystem_id'])
                # if not state:
                #     return JsonResponse({'message': msg, 'code': 500})
                # 项目用例全部查询
                if not detail:
                    case_list = ''
                    if type_choose:
                        module_sql = SELECT_MODULE_LIST % (subsystem_id, type_choose)
                    else:
                        module_sql = SELECT_NO_MODULE_LIST % (subsystem_id)
                    module_list = MySQLHelper().get_all(module_sql)
                    if module_list:
                        module_case_list = []
                        for item in module_list:
                            module_case_list.append(dict(zip(['id', 'case_list', 'parent_id'], item)))
                        module_list = list_to_tree(module_case_list)
                        case_list = get_str(case_list, module_list)
                    if case_list:
                        if type_choose:
                            sql = SELECT_CASE_LIST % (
                            username, state_choose, state_choose, type_choose, case_list, case_list)
                        else:
                            sql = SELECT_CASE_LIST_NOTYPE % (
                            username, state_choose, state_choose, case_list, case_list)
                        case_interface_list = MySQLHelper().get_all(sql)
                    else:
                        case_interface_list = []
                else:  # 项目用例模糊查询
                    if type_choose:
                        sql = CASE_LIST_LIKE % (username, subsystem_id, type_choose, state_choose, state_choose, detail)
                    else:
                        sql = CASE_LIST_LIKE_NOTYPE % (username, subsystem_id, state_choose, state_choose, detail)
                    case_interface_list = MySQLHelper().get_all(sql)
                    case_interface_list = case_interface_list if case_interface_list else []
            i = (int(page) - 1) * int(limit)
            j = (int(page) - 1) * int(limit) + int(limit)
            total = len(case_interface_list)
            if total > 10:
                sub_case_interface = case_interface_list[i:j]
            else:
                sub_case_interface = case_interface_list
            sql_params = [
                'id', 'case_name', 'req_path', 'req_method', 'extract_list',
                'update_time', 'username', 'state', 'creator']
            try:
                data = convert_data(sub_case_interface, sql_params)
            except Exception as e:
                print(e)
                msg = SERVER_ERROR
                data = []
            result_dict['code'] = 0
            result_dict['msg'] = msg if msg else ""
            result_dict['count'] = total
            result_dict['data'] = data
            return JsonResponse(result_dict, safe=False)
        else:
            # 模块用例树形图
            # subsystem_id = param.get("subsystem_id", "")
            module_list = Sys_module.objects.filter(subsystem_id=subsystem_id, is_delete=0)
            module_list_str = ','.join([module.case_list for module in module_list if module.case_list]).strip(
                ',') if module_list else ''
            # 用例查询sql语句
            case_info = ()
            if module_list_str:
                sql = CASE_LIST % (module_list_str, module_list_str)
                case_info = MySQLHelper().get_all(sql)
            ret = MySQLHelper().get_all(MODULE_LIST_TREE, (username, subsystem_id))
            # 用例根节点
            path_ret = MySQLHelper().get_all(MODULE_PATH, (subsystem_id,))
            path = path_ret[0][0] if path_ret else ""
            if not ret:
                return JsonResponse({'data': [{"title": path,
                                               "id": subsystem_id,
                                               'level': 0}],
                                     }, safe=False)
            ret = convert_data(ret + case_info, ['id', 'title', 'parent_id', 'level', 'report_path', 'module_type'])
            result = list_to_tree(ret)
            all_result = [{"title": path, "id": subsystem_id,
                           "children": result, 'level': 0, 'spread': True}]
            return JsonResponse({'data': all_result, 'msg':'ok', 'code':0}, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 用例新增
@login_check
def case_add(request):
    username = request.session.get('username', '')
    if request.method == 'POST':
        # 用例接口添加
        param_list, result_dict, msg = ['module_id', 'interface_id', 'case_name', 'req_path', 'req_method'], {}, 'ok'
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        module_id = params.get('module_id', '')
        interface_id = params.get('interface_id', '')
        case_name = params.get('case_name', '')
        req_path = params.get('req_path', '')
        req_method = params.get('req_method', '')
        req_headers = convert_to_json(params.get('req_headers')) if params.get('req_headers', '') else ''
        req_param = convert_to_json(params.get('req_param')) if params.get('req_param', '') else ''
        req_body = convert_to_json(params.get('req_body')) if params.get('req_body', '') else ''
        req_file = convert_to_json(params.get('req_file')) if params.get('req_file', '') else ''
        run_time = params.get('run_time', '').strip()
        wait_time = params.get('wait_time', '').strip()
        except_list = json.dumps(params.get('except_list'), ensure_ascii=False) if params.get('except_list', '') else ''
        extract_list = params.get('extract_list', '')
        extract_id, create_list, rule_name = '', [], []
        module_permission = MySQLHelper().get_all(GET_PERSON_MODULE, (username, module_id))
        module_info = Sys_module.objects.filter(id=module_id, is_delete=0)
        if not module_info:
            return JsonResponse({'message': MODULE_NOT_FOUND, 'code': 500})
        subsystem_id = module_info[0].subsystem_id
        project_id = Sys_subsystem.objects.get(id=subsystem_id).project_id
        if module_permission:
            sql = CHECK_CASE_NAME_EXIST % (subsystem_id, case_name)
            case_name_exist = MySQLHelper().get_all(sql)
            # case_name_exist = Inte_case.objects.filter(case_name=case_name, is_delete=0)
            if case_name_exist:
                return JsonResponse({"message": CASE_NAME_EXIST, "code": 500})
            if extract_list:
                for rule in extract_list:
                    extract_name = rule['name']
                    extract_rule = rule['rule']
                    data_format = rule['dataFormat']
                    if Inte_extract.objects.filter(param_name=extract_name, project_id=project_id,
                                                   subsystem_id=subsystem_id, is_delete=0):
                        return JsonResponse({'message': EXTRACT_NAME_REPRTITION, 'code': 500})
                    create_list.append(
                        Inte_extract(param_name=extract_name, rule=extract_rule, data_format=data_format,
                                     username=username, project_id=project_id, subsystem_id=subsystem_id))
                    rule_name.append(rule['name'])
                try:
                    Inte_extract.objects.bulk_create(create_list)
                except Exception as e:
                    print(e)
                    return JsonResponse({'message': EXTRACT_NAME_REPRTITION, 'code': 500})
            if rule_name:
                id_result = MySQLHelper().get_all(SELECT_EXTRACT_ID, (project_id, subsystem_id, tuple(rule_name)))
            else:
                id_result = []
            extract_id = ",".join([str(x[0]) for x in id_result])
            case_id = Inte_case.objects.create(
                module_id=int(module_id),
                interface_id=int(interface_id),
                case_name=case_name,
                req_path=req_path,
                req_headers=req_headers,
                req_param=req_param,
                req_body=req_body,
                req_file=req_file,
                username=username,
                req_method=req_method,
                extract_list=extract_id,
                except_list=except_list,
                case_type=module_info[0].module_type,
                run_time=run_time,
                wait_time=wait_time,
                creator=username).id
            new_case_id = Inte_case.objects.filter(module_id=module_id).order_by('-id')[0].id
            case_if_list = module_info[0].case_list + ',' + str(new_case_id)
            module_info.update(case_list=case_if_list.lstrip(','))
            # 重复保存去除提取参数提示
            params_id = Inte_case.objects.filter(id=case_id)[0].extract_list
            params_list = sorted(params_id.split(',')) if params_id else []

            context = {'message': ADD_SUCCESS_200, 'code': 200, 'id': case_id, 'params_list': params_list}
            object_desc = case_name + '(' + str(case_id) + ')'
            user_operate(username, "be_add", "ob_case", object_desc)  # 用户操作记录日志
        else:
            context = {'message': NOT_PERMISSION, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 用例编辑
@login_check
def case_edit(request, id):
    username = request.session.get('username', '')
    if request.method == 'GET':
        username = request.session.get('username', '')
        case_param = ["id", "interface_id", "case_name", "req_path", "req_method", "req_headers", "req_param",
                      "req_body", "req_file", "extract_list", "except_list", "run_time", "wait_time", "module_id"]
        case_interface_info = convert_one_to_many_data(MySQLHelper().get_all(SELECT_CASE_INFO,
                                                                             (username, id)), case_param, 1)
        return JsonResponse({'message': 'ok', 'code': 200, 'data': case_interface_info})

    elif request.method == 'POST':
        param_list = ["interface_id", "case_name", "req_path", "req_method", "run_time", "module_id"]
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        case_name = params.get('case_name', '').strip()
        interface_id = params.get('interface_id', '')
        req_path = params.get('req_path', '')
        req_headers = convert_to_json(params.get('req_headers')) if params.get('req_headers', '') else ''
        req_param = convert_to_json(params.get('req_param')) if params.get('req_param', '') else ''
        req_body = convert_to_json(params.get('req_body')) if params.get('req_body', '') else ''
        req_file = json.dumps(params.get('req_file'), ensure_ascii=False) if params.get('req_file', '') else ''
        req_method = params.get('req_method', '')
        module_id = params.get('module_id', '').strip()
        run_time = params.get('run_time', 1).strip()
        wait_time = params.get('wait_time', 0).strip()
        except_list = json.dumps(params.get('except_list'), ensure_ascii=False) if params.get('except_list', '') else ''
        extract_list = params.get('extract_list', '')
        update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        module_info = Sys_module.objects.filter(id=module_id, is_delete=0)
        if not module_info:
            return JsonResponse({'message': MODULE_NOT_FOUND, 'code': 500})
        subsystem_id = module_info[0].subsystem_id
        project_id = Sys_subsystem.objects.get(id=subsystem_id).project_id

        project_permission = MySQLHelper().get_all(GET_PERSON_MODULE, (username, module_id))
        if project_permission:
            if int(id):
                case_name_other_exist = MySQLHelper().get_all(CASE_NAME_OTHER_EXIST, (subsystem_id, case_name, id))
                if case_name_other_exist:
                    return JsonResponse({"message": CASE_NAME_EXIST, "code": 500})
                interface_extract = Inte_extract.objects
                extract_id, create_list, extract_name_list, update_objs, new_extract_id, old_extract_id \
                    = '', [], [], [], [], []
                if extract_list:
                    for rule_dict in extract_list:
                        extract_name = rule_dict['name']
                        extract_rule = rule_dict['rule']
                        data_format = rule_dict['dataFormat']
                        if "id" in rule_dict.keys() and rule_dict['id'] != 'undefined':
                            if Inte_extract.objects.filter(param_name=extract_name, project_id=project_id,
                                                           subsystem_id=subsystem_id,
                                                           is_delete=0).exclude(id=int(rule_dict['id'])):
                                return JsonResponse({'message': EXTRACT_NAME_REPRTITION, 'code': 500})
                            update_info = interface_extract.filter(id=rule_dict['id'])[0]
                            if update_info:
                                update_info.param_name = extract_name
                                update_info.rule = extract_rule
                                update_info.data_format = data_format
                                update_objs.append(update_info)
                        else:
                            if Inte_extract.objects.filter(param_name=extract_name, project_id=project_id,
                                                           subsystem_id=subsystem_id, is_delete=0):
                                return JsonResponse({'message': EXTRACT_NAME_REPRTITION, 'code': 500})
                            create_list.append(
                                Inte_extract(param_name=extract_name, rule=extract_rule, data_format=data_format,
                                             project_id=project_id, subsystem_id=subsystem_id, username=username))
                        extract_name_list.append(extract_name)
                    try:
                        bulk_update(update_objs)
                    except Exception as e:
                        print(e)
                        return JsonResponse({'message': EXTRACT_NAME_REPRTITION, 'code': 500})
                    if create_list:
                        try:
                            Inte_extract.objects.bulk_create(create_list)
                        except Exception as e:
                            print(e)
                            return JsonResponse({'message': EXTRACT_NAME_REPRTITION, 'code': 500})

                    id_result = MySQLHelper().get_all(SELECT_EXTRACT_ID,
                                                      (project_id, subsystem_id, tuple(extract_name_list)))
                    extract_id = ",".join([str(x[0]) for x in id_result])

                    new_extract_id = extract_id.split(",")
                case_info = Inte_case.objects.filter(id=id)
                old_extract_id = case_info[0].extract_list.split(',') if case_info[
                    0].extract_list else []
                del_list = [del_old_id for del_old_id in old_extract_id if del_old_id not in new_extract_id]
                interface_extract.filter(id__in=del_list).delete()
                case_info.update(
                    interface_id=int(interface_id),
                    case_name=case_name,
                    req_path=req_path,
                    req_headers=req_headers,
                    req_param=req_param,
                    req_body=req_body,
                    req_file=req_file,
                    username=username,
                    req_method=req_method,
                    extract_list=extract_id,
                    except_list=except_list,
                    run_time=run_time,
                    wait_time=wait_time,
                    update_time=update_time)
                # 重复保存去除提取参数提示
                params_id = case_info[0].extract_list
                params_list = sorted(params_id.split(',')) if params_id else []

                context = {'message': EDIT_SUCCESS_200, 'id': id, 'code': 200, 'params_list': params_list}
                object_desc = case_name + '(' + str(id) + ')'
                user_operate(username, "be_edit", "ob_case", object_desc)  # 用户操作记录日志
            else:
                context = {'message': EDIT_FAIL_500, 'code': 500}
        else:
            context = {'message': NOT_PERMISSION, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 用例删除
@login_check
def case_delete(request):
    username = request.session.get("username", "")
    if request.method == 'POST':
        # 删除所有
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get("ids")
        map_ids = map(str, ids)  # 格式化
        str_ids = ",".join(map_ids)  # 转换成 str 类型
        # 权限校验
        sql = DELETE_CASE_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        del_ids = []
        if type(ids) == list:
            # 校验用例是否被任务勾选
            task_sql = SELECT_CASE_TO_TASK % (str_ids, str_ids)
            case_id_exist = convert_data(MySQLHelper().get_all(task_sql), ['case_id'])
            if case_id_exist:
                id = case_id_exist[0]["case_id"]
                case_name = Inte_case.objects.get(id=int(id)).case_name
                return JsonResponse({"message": "用例【%s】已被任务使用，不允许删除！" % case_name, "code": 500})
            for id in ids:
                case_info = Inte_case.objects.filter(id=id)
                if case_info[0].extract_list:
                    Inte_extract.objects.filter(id__in=case_info[0].extract_list.split(',')).delete()
                    # Inte_extract.objects.filter(id__in=case_info[0].extract_list.split(',')).update(is_delete=1)
                case_info.update(is_delete=1, username=username, update_time=get_time())
                module_id = case_info[0].module_id
                case_if_list = Sys_module.objects.filter(id=module_id)[0].case_list.split(',')
                case_if_list.remove(str(id))
                Sys_module.objects.filter(id=module_id).update(case_list=','.join(case_if_list))
                del_ids.append(id)
            if len(ids) == len(del_ids):
                context = {'message': DEL_SUCCESSS_200, 'code': 200}
                user_operate(username, "be_del", "ob_case", str_ids)  # 用户操作记录日志
            else:
                context = {'message': DEL_FAIL_500, 'code': 500}
            return JsonResponse(context)
        return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 用例上下移动顺序
@login_check
def case_upAndDown(request):
    username = request.session.get("username", "")
    if request.method == 'POST':
        param_list = ['module_id', 'if_id', 'mode']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        module_id = param.get("module_id", "")
        if_id = param.get("if_id", "")
        mode = param.get("mode", "")
        # 根据模块id关联权限表
        project_permission = MySQLHelper().get_all(GET_PERSON_MODULE, (username, module_id))
        if not project_permission:
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        if_list = Sys_module.objects.get(id=module_id).case_list
        if type(if_id) != list or not if_id:
            return JsonResponse({'message': 'if_id' + NOT_LIST, 'code': 200})
        if_id_str = (",".join(map(str, if_id))).strip(',')
        if if_id_str not in if_list:
            return JsonResponse({"message": "只能勾选相邻用例！", "code": 500})
        if_list_up = if_list.split(',')
        if mode == "up":  # 上移
            try:
                if str(if_id[0]) == if_list_up[0]:
                    return JsonResponse({'message': "已经是最前一条了", 'code': 500})
                for i in if_id:
                    if_index = if_list_up.index(str(i))
                    if_list_up[if_index - 1], if_list_up[if_index] = if_list_up[if_index], if_list_up[if_index - 1]
                if_result = (",".join(str(i) for i in if_list_up))
                Sys_module.objects.filter(id=module_id).update(case_list=if_result)
                context = {'message': MOVE_SUCCESS_200, 'code': 200}
                object_desc = "移动ID:" + if_id_str + ",移动后位置:" + if_result
                user_operate(username, "be_up", "ob_case", object_desc)  # 用户操作记录日志
            except Exception as e:
                print(e)
                context = {'message': MOVE_FAIL_500, 'code': 500}
            return JsonResponse(context)
        elif mode == "down":  # 下移
            try:
                len_if_id = len(if_id)
                if str(if_id[-1]) == if_list_up[-1]:
                    return JsonResponse({'message': "已经是最后一条了", 'code': 500})
                for i in if_id:
                    if_index = if_list_up.index(str(i))
                    if_list_up[if_index], if_list_up[if_index + len_if_id] = if_list_up[if_index + len_if_id], \
                                                                             if_list_up[
                                                                                 if_index]
                    len_if_id -= 1
                if_result = (",".join(str(i) for i in if_list_up))
                Sys_module.objects.filter(id=module_id).update(case_list=if_result)
                context = {'message': MOVE_SUCCESS_200, 'code': 200}
                object_desc = "移动ID:" + if_id_str + ",移动后位置:" + if_result
                user_operate(username, "be_down", "ob_case", object_desc)  # 用户操作记录日志
            except Exception as e:
                print(e)
                context = {'message': MOVE_FAIL_500, 'code': 500}
            return JsonResponse(context)
        else:
            return JsonResponse({"message": "mode值错误！", "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 递归获取模块id

def get_case_list(module_id, case_list_str=''):
    ret = MySQLHelper().get_all("select id, case_list from sys_module where parent_id=%s", (module_id,))
    for i in ret:
        case_list_str += ',' + i[1] if i[1] else ''
        get_case_list(i[0], case_list_str)
    return case_list_str


# 执行用例集接口
@login_check
def execute_cases(request, id):
    username = request.session.get("username", "")
    # 根据模块id关联权限表
    project_permission = MySQLHelper().get_all(GET_PERSON_MODULE, (username, id))
    if not project_permission:
        return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
    if request.method == "POST":
        try:
            module_info = Sys_module.objects.filter(id=id, is_delete=0)[0]
        except:
            pass
        finally:
            if not module_info.case_list:
                return JsonResponse({"message": "用例为空", "code": 404})
        # 前置用例
        before_info = Sys_module.objects.filter(subsystem_id=module_info.subsystem_id, is_delete=0, module_type=2)[0]

        # 后置用例
        after_info = Sys_module.objects.filter(subsystem_id=module_info.subsystem_id, is_delete=0, module_type=3)[0]
        if not before_info.env_id:
            return JsonResponse({"message": "请为" + before_info.module_name + "添加环境", "code": 404})
        if not after_info.env_id:
            return JsonResponse({"message": "请为" + after_info.module_name + "添加环境", "code": 404})
        before_case = get_case_list(before_info.id) + ',' + before_info.case_list
        after_case = get_case_list(after_info.id) + ',' + after_info.case_list
        case_list = get_case_list(module_info.id) + ',' + module_info.case_list
        case_list = before_case.strip(',') + "," + case_list.strip(',') + "," + after_case.strip(',')
        case_list_sql = EXECUTE_CASE_LIST % (username, case_list.strip(","), case_list.strip(","))
        sql_result = MySQLHelper().get_all(case_list_sql)
        # 版本接口总数
        interface_count = len(
            Inte_interface.objects.filter(is_delete=0, state=1, subsystem_id=module_info.subsystem_id))
        case_name = module_info.module_name
        project_id = Sys_subsystem.objects.get(id=module_info.subsystem_id).project_id
        case_detail = []
        for case_info in sql_result:
            extract_list = case_info[12] if case_info[12] else ''
            if extract_list:
                sql = SELECT_INTERFACE_EXTRACT_LIST % "(" + extract_list + ")"
                extract_list = convert_data(MySQLHelper().get_all(sql), ['id', 'name', 'rule', 'data_format'])
            interface_data = {
                'id': case_info[0],
                'case_name': case_info[1],
                'module_id': case_info[2],
                'module_name': case_info[3],
                'host': case_info[4],
                'port': case_info[5],
                'req_method': case_info[6],
                'req_path': case_info[7],
                'req_headers': case_info[8],
                'req_param': case_info[9],
                'req_body': case_info[10],
                'req_file': case_info[11],
                'extract_list': extract_list,
                'except_list': case_info[13],
                'subsystem_id': case_info[14],
                'run_time': case_info[15],
                'module_type': case_info[16],
                'interface_id': case_info[17],
                'project_id': str(case_info[18]),
                'wait_time': case_info[19],
                'interface_count': interface_count,
                'type': 'case'
            }
            for t in range(0, interface_data['run_time']):
                case_detail.append(interface_data)

        # 执行测试用例
        username = request.session.get("username", '')
        return runCase(case_detail, id, username, case_name, project_id)


# 测试用例集执行
def runCase(case_detail, case_id, username, report_name, project_id):
    """
    :param case_detail: 用例详情列表
    :param case_id: 用例集id
    :param username: 操作人
    :param report_name: 用例集名称
    :param project_id: 项目id
    :return: 执行结果
    """
    result_file = ''
    try:
        response, result_file = Test.test_suite(case_detail, "case", case_id, username, report_name, project_id)
        case_desc = None
        for res_data in response:
            if '失败' == res_data[5]:
                break
        else:
            case_desc = 1
        if case_desc:
            content = {"message": EXECUTE_CASE_SUCCESS, "code": 200, 'id': case_id, 'report_path': result_file}
        else:
            content = {"message": EXECUTE_CASE_FAIL, "code": 500, 'id': case_id, 'report_path': result_file}
        object_desc = report_name + '(' + str(case_id) + ')'
        user_operate(username, "be_now_run", "ob_module", object_desc)  # 用户操作记录日志
        return JsonResponse(content)
    except BaseException as e:
        content = {
            "message": EXECUTE_CASE_EXCEPT % str(e),
            "code": 500,
            'id': case_id,
            'report_path': result_file
        }
        return JsonResponse(content)


# 数据库工具环境管理
@login_check
def database_env_manager(request):
    username = request.session.get("username", "")
    if request.method == "GET":
        pass
        # return render(request, 'database/database-list.html')
    elif request.method == "POST":
        param_list, result_dict, msg = ['project_id'], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        env_name = param.get("env_name", '')
        project_id = param.get("project_id", '')
        page = param.get("page", 1)
        limit = param.get("limit", 10)
        # 检验参数
        i = (int(page) - 1) * int(limit)
        j = (int(page) - 1) * int(limit) + int(limit)
        sql = DATABASE_ENV_LIST_LIKE % (username, env_name, project_id)
        database_env_list = MySQLHelper().get_all(sql)
        sub_case = database_env_list[i:j]
        total = len(database_env_list)
        database_env_params = [
            'id', 'project_name', 'type', 'ip', 'env_name', 'env_port',
            'user', 'password', 'dbname', 'env_desc', 'update_time',
            'username', 'creator'
        ]
        try:
            data = convert_data(sub_case, database_env_params)
        except Exception as e:
            print(e)
            msg = SERVER_ERROR
            data = []
        result_dict['code'] = 0
        result_dict['msg'] = msg if msg else ""
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 数据库工具环境新增
@login_check
def database_env_add(request):
    username = request.session.get("username", "")
    if request.method == 'POST':
        param_list = ['env_name', 'project_id', 'ip', 'env_port','type','dbname','password',]
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        env_name = param.get('env_name', '').strip()
        project_id = param.get('project_id', '').strip()
        ip = param.get('ip', '').strip()
        env_port = param.get('env_port', '').strip()
        env_desc = param.get('env_desc', '').strip()
        user = param.get('user', '').strip()
        password = param.get('password', '').strip()
        dbname = param.get('dbname', '').strip()
        db_type = param.get('type', '')
        project_permission = MySQLHelper().get_all(GET_PERSON_PROJECT, (username, project_id))
        if project_permission:
            name_exist = Sys_db_env.objects.filter(env_name=env_name, project_id=project_id, is_delete=0)
            if name_exist:  # 判断名称重复
                return JsonResponse({"message": NAME_REPETITION, "code": 500})
            if type == "1":
                state, param = params_secrect(param, ['user', 'password', 'dbname'])
                if not state:
                    return JsonResponse({'message': param, 'code': 500})
            id = Sys_db_env.objects.create(
                project_id=project_id,
                db_type=db_type,
                env_ip=ip,
                env_name=env_name,
                env_port=env_port,
                user=user,
                password=password,
                dbname=dbname,
                env_desc=env_desc,
                username=username,
                creator=username).id
            object_desc = env_name + '(' + str(id) + ')'
            user_operate(username, "be_add", "ob_db_driven", object_desc)  # 用户操作记录日志
            context = {'message': ADD_SUCCESS_200, 'code': 200}
        else:
            context = {'message': NOT_PERMISSION, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 数据库工具环境编辑
@login_check
def database_env_edit(request, id):
    username = request.session.get("username", "")

    # 根据数据库环境id关联权限表
    perject_permission = MySQLHelper().get_all(DB_ENV_OPERATE, (username, id))
    if not perject_permission:
        return {'message': NOT_PERMISSION, 'code': 500}
    if request.method == 'GET':
        env_result = MySQLHelper().get_all(SELECT_DATABASE_ENV_INFO, (username, id))
        database_env_params = [
            'id', 'project_id', 'type', 'ip', 'env_name', 'env_port', 'user',
            'password', 'dbname', 'env_desc', 'update_time', 'username'
        ]
        env_info = convert_data(env_result, database_env_params)
        return JsonResponse({'message': 'ok', 'code': 200, 'data': env_info[0] if env_info else []})
    elif request.method == 'POST':
        param_list, result_dict, msg = ['env_name', 'project_id', 'ip', 'env_port', 'type'], {}, 'ok'
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        env_name = params.get('env_name', '').strip()
        project_id = params.get('project_id', '')
        ip = params.get('ip', '').strip()
        env_port = params.get('env_port', '').strip()
        env_desc = params.get('env_desc', '').strip()
        user = params.get('user', '').strip()
        password = params.get('password', '').strip()
        dbname = params.get('dbname', '').strip()
        db_type = params.get('type', '')
        project_permission = MySQLHelper().get_all(GET_PERSON_PROJECT,
                                                   (username, project_id))
        if project_permission:
            if int(id):
                if type == "1":
                    state, param = params_secrect(params, ['user', 'password', 'dbname'])
                    if not state:
                        return JsonResponse({'message': param, 'code': 500})
                name_exist = Sys_db_env.objects.filter(env_name=env_name, project_id=project_id, is_delete=0).exclude(
                    id=id)
                if name_exist:  # 判断名称重复
                    return JsonResponse({"message": NAME_REPETITION, "code": 500})
                database_env_info = Sys_db_env.objects.filter(id=id, is_delete=0)
                try:
                    database_env_info.update(
                        project_id=project_id,
                        db_type=db_type,
                        env_ip=ip,
                        env_name=env_name,
                        env_port=env_port,
                        user=user,
                        password=password,
                        dbname=dbname,
                        env_desc=env_desc,
                        username=username,
                        update_time=get_time())
                    context = {'message': EDIT_SUCCESS_200, 'code': 200}
                    object_desc = env_name + '(' + str(id) + ')'
                    user_operate(username, "be_edit", "ob_db_driven", object_desc)  # 用户操作记录日志
                except Exception as e:
                    print(e)
                    context = {'message': EDIT_FAIL_500, 'code': 500}
            else:
                context = {'message': EDIT_FAIL_500, 'code': 500}
        else:
            context = {'message': NOT_PERMISSION, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 数据库工具环境删除
@login_check
def database_env_delete(request):
    username = request.session.get("username", "")
    if request.method == 'POST':
        # 删除所有
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get("ids")
        # 权限校验
        map_ids = map(str, ids)  # 格式化
        str_ids = ",".join(map_ids)  # 转换成 str 类型
        sql = DELETE_DB_ENV_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        del_ids = []
        env_name = []
        if type(ids) != int:
            for id in ids:
                name = Sys_db_env.objects.get(id=id).env_name
                sql = Sys_db_sqldetail.objects.filter(env_id=id, is_delete=0)
                if not sql:
                    Sys_db_env.objects.filter(id=id, is_delete=0).update(
                        is_delete=1, username=username, update_time=get_time())
                    del_ids.append(id)
                    env_name.append(name)
            if len(ids) == len(del_ids):
                object_desc = ",".join(map(str, env_name)) + '(' + str_ids + ')'
                user_operate(username, "be_del", "ob_db_driven", object_desc)  # 用户操作记录日志
                context = {'message': DEL_SUCCESSS_200, 'code': 200}
            else:
                context = {'message': "删除失败，与sql存在关联关系！", 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 数据库环境sql语句管理
@login_check
def database_statement_manager(request):
    username = request.session.get("username", "")
    if request.method == "GET":
        pass
        # return render(request, 'database/sql-list.html')
    elif request.method == "POST":
        param_list = ['db_env_id']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        sql_name = param.get("sql_name", '')
        db_env_id = param.get("db_env_id", '')
        page = param.get("page", 1)
        limit = param.get("limit", 10)
        total, data, result_dict, msg = 0, [], {}, ''
        # 检验参数
        i = (int(page) - 1) * int(limit)
        j = (int(page) - 1) * int(limit) + int(limit)
        sql = SQL_LIST_LIKE % (username, sql_name, db_env_id)
        database_statement_list = MySQLHelper().get_all(sql)
        sub_case = database_statement_list[i:j]
        total = len(database_statement_list)
        database_statement_params = [
            'id', 'sql_name', 'sql', 'state', 'result', 'update_time', 'username', 'remark'
        ]
        try:
            data = convert_data(sub_case, database_statement_params)
        except Exception as e:
            print(e)
            msg = SERVER_ERROR
            data = []
        result_dict['code'] = 0
        result_dict['msg'] = msg if msg else ""
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)


# 数据库工具sql语句新增
@login_check
def database_statement_add(request):
    username = request.session.get("username", "")
    if request.method == 'POST':
        param_list = ['env_id', 'sql_name', 'sql']
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        env_id = params.get('env_id', '')
        sql_name = params.get('sql_name', '')
        sql = params.get('sql', '').strip()
        remark = params.get('remark', '').strip()
        result = params.get('result', '').strip()
        project_permission = MySQLHelper().get_all(GET_PERSON_DATABASE_ENV,
                                                   (username, env_id))
        if project_permission:
            name_exist = Sys_db_sqldetail.objects.filter(sql_name=sql_name, env_id=env_id, is_delete=0)
            if name_exist:  # 判断名称重复
                return JsonResponse({"message": NAME_REPETITION, "code": 500})
            try:
                id = Sys_db_sqldetail.objects.create(
                    sql_name=sql_name,
                    env_id=env_id,
                    sql=sql,
                    remark=remark,
                    result=result,
                    username=username).id
                object_desc = sql_name + '(' + str(id) + ')'
                user_operate(username, "be_add", "ob_db_sql", object_desc)  # 用户操作记录日志
                context = {'message': ADD_SUCCESS_200, 'code': 200}
            except:
                context = {'message': NAME_REPETITION, 'code': 500}
        else:
            context = {'message': NOT_PERMISSION, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message":NOT_METHMOD,"code":500})

# 数据库工具sql语句编辑
@login_check
def database_statement_edit(request, id):
    username = request.session.get("username", "")
    if request.method == 'GET':
        database_statement_params = [
            'id', 'sql_name', 'sql', 'remark', 'result'
        ]
        database_statement_info = convert_data(
            MySQLHelper().get_all(SQL_DETAIL_INFO, (username, id)), database_statement_params)
        return JsonResponse(
            {'message': 'ok', 'code': 200, 'data': database_statement_info[0] if database_statement_info else []})
    elif request.method == 'POST':
        param_list = ['env_id', 'sql_name', 'sql']
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        env_id = params.get('env_id', '')
        sql_name = params.get('sql_name', '').strip()
        sql = params.get('sql', '').strip().strip()
        remark = params.get('remark', '').strip()
        result = params.get('result', '').strip()
        project_permission = MySQLHelper().get_all(
            GET_PERSON_DATABASE_STATEMENT, (username, id))
        if project_permission:
            if int(id):
                name_exist = Sys_db_sqldetail.objects.filter(sql_name=sql_name, env_id=env_id, is_delete=0).exclude(
                    id=id)
                if name_exist:  # 判断名称重复
                    return JsonResponse({"message": NAME_REPETITION, "code": 500})
                database_env_info = Sys_db_sqldetail.objects.filter(id=id)
                try:
                    database_env_info.update(
                        env_id=env_id,
                        sql_name=sql_name,
                        sql=sql,
                        username=username,
                        remark=remark,
                        result=result,
                        update_time=get_time())
                    context = {'message': EDIT_SUCCESS_200, 'code': 200}
                    object_desc = sql_name + '(' + str(id) + ')'
                    user_operate(username, "be_edit", "ob_db_sql", object_desc)  # 用户操作记录日志
                except Exception as e:
                    print(e)
                    context = {'message': EDIT_FAIL_500, 'code': 200}
            else:
                context = {'message': EDIT_FAIL_500, 'code': 500}
        else:
            context = {'message': NOT_PERMISSION, 'code': 500}
        return JsonResponse(context)


# 数据库工具sql语句删除
@login_check
def database_statement_delete(request, id=None):
    username = request.session.get("username", "")
    if request.method == 'POST':
        # 删除所有
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get("ids")
        # 权限校验
        map_ids = map(str, ids)  # 格式化
        str_ids = ",".join(map_ids)  # 转换成 str 类型
        sql = DELETE_DB_SQL_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        del_ids = []
        sql_name = []
        if type(ids) != int:
            for id in ids:
                name = Sys_db_sqldetail.objects.get(id=id).sql_name
                Sys_db_sqldetail.objects.filter(id=id, is_delete=0).update(
                    is_delete=None, username=username, update_time=get_time())
                del_ids.append(id)
                sql_name.append(name)
            if len(ids) == len(del_ids):
                context = {'message': DEL_SUCCESSS_200, 'code': 200}
                object_desc = ",".join(map(str, sql_name)) + '(' + str_ids + ')'
                user_operate(username, "be_del", "ob_db_sql", object_desc)  # 用户操作记录日志
            else:
                context = {'message': DEL_FAIL_500, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 数据库工具操作
@login_check
def database_operate(request, scoure=None):
    if request.method == "POST":
        state, params = params_check(request.body, [])
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        sql = params.get('sql', '')
        if scoure == 'sql':# 查询请求
            state, msg = params_secrect(params, ['env_id', 'sql'])
            if not state:
                return JsonResponse({'message': msg, 'code': 500})
            env_id = params.get('env_id', '')
            sql = params.get('sql', '')
            env_info = Sys_db_env.objects.get(id=env_id)
            if env_info:
                result, message, ret = database_query(type=env_info.db_type, host=env_info.env_ip,
                                                      port=int(env_info.env_port),
                                                      user=env_info.user, password=env_info.password,
                                                      db=env_info.dbname, sql=sql)
                if ret == 0:
                    return JsonResponse({'data': result, 'message': message, 'code': 200})
                else:
                    return JsonResponse({'data': result, 'message': message, 'code': 500})
            return JsonResponse({'message': [], 'code': 200})
        else:# 连接测试
            state, msg = params_secrect(params, ['ip', 'env_port', 'type', 'user', 'password', 'dbname'])
            if not state:
                return JsonResponse({'message': msg, 'code': 500})
            type = params.get('type', '')
            ip = params.get('ip', '')
            port = params.get('env_port', '')
            user = params.get('user', '')
            password = params.get('password', '')
            dbname = params.get('dbname', '')
            type = str(type)
            if type == '1':
                result = MySQLObj(host=ip, port=int(port), user=user, password=password, db=dbname).connect()
            elif type == "2":
                result = RedisObj().connect_test(host=ip, port=int(port), password=password)
            elif type == "3":
                result = MongoObj(ip, int(port), dbname, user, password).connect()
            else:
                return JsonResponse({'message': '没有这个类型数据库!', 'code': 500})
            if not isinstance(result, dict):
                return JsonResponse({'message': DATABASE_CONNECT_SUCCESSS, 'code': 200})
            else:
                return JsonResponse({'message': DATABASE_CONNECT_FAIL, 'code': 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 用例模块报告
@login_check
def case_report(request):
    if request.method == "GET":
        pass
        # return render(request, 'interface/case_report.html', {"case_id": id})
    elif request.method == "POST":
        state, param = params_check(request.body, ['id'])
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        page = param.get('page', 1)
        rows = param.get("limit", 10)
        id = param.get("id", '')
        i = (int(page) - 1) * int(rows)
        j = (int(page) - 1) * int(rows) + int(rows)
        report_list = MySQLHelper().get_all(CASE_REPORT_LIST, (id,))
        sql_params = [
            'id', 'case_name', 'report_type', 'report_path', 'file_name',
            'update_time', 'username'
        ]
        sub_report = report_list[i:j]
        data = convert_data(sub_report, sql_params)
        total = len(report_list)
        result_dict = {}
        result_dict['code'] = 0
        result_dict['msg'] = ""
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})

# 报告列表
@login_check
def report_list(request):
    if request.method == "GET":
        pass
        # return render(request, 'report/report-list.html')
    elif request.method == "POST":
        param_list, result_dict, msg = ["project_id"], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        username = request.session.get("username", "")
        report_name = param.get("report_name", '')
        project_id = param.get("project_id", '')
        page = param.get('page', 1)
        rows = param.get("limit", 10)
        i = (int(page) - 1) * int(rows)
        j = (int(page) - 1) * int(rows) + int(rows)
        sql = REPORT_LIST_LIKE % (username, report_name, project_id)
        report_list = MySQLHelper().get_all(sql)
        sub_report = report_list[i:j]
        total = len(report_list)
        sql_params = ['id', 'task_name', 'report_path', 'file_name', 'report_type', 'update_time', 'username']
        try:
            data = convert_data(sub_report, sql_params)
        except Exception as e:
            print(e)
            msg = SERVER_ERROR
            data = []
        result_dict = {}
        result_dict['code'] = 0
        result_dict['msg'] = msg
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})

# 删除报告
@login_check
def report_del(request):
    if request.method == "POST":
        username = request.session.get('username', '')
        state, param = params_check(request.body, ['ids'])
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get('ids', '')
        map_ids = map(str, ids)  # 格式化
        str_ids = ",".join(map_ids)  # 转换成 str 类型
        sql = DELETE_REPORT_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        del_ids = []
        sql_name = []
        if type(ids) == list:
            for id in ids:
                name = Inte_report.objects.get(id=id).file_name
                Inte_report.objects.filter(id=id, is_delete=0).update(
                    is_delete=1, username=username, update_time=get_time())
                del_ids.append(id)
                sql_name.append(name)
            if len(ids) == len(del_ids):
                context = {'message': DEL_SUCCESSS_200, 'code': 200}
                object_desc = ",".join(map(str, sql_name)) + '(' + str_ids + ')'
                user_operate(username, "be_del", "ob_report", object_desc)  # 用户操作记录日志
            else:
                context = {'message': DEL_FAIL_500, 'code': 500}
            return JsonResponse(context)
        return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})

# 报告导出
@login_check
def report_export_new(request):
    if request.method == "POST":
        state, params = params_check(request.body, ['export_type'])
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        username = request.session.get("username", "")
        export_type =  params.get("export_type", 0) # 0 导出项目全部报告，1导出任务下的报告
        project_id = params.get("project_id", "")
        task_id = params.get("task_id", "")
        permission = MySQLHelper().get_all(PROJECT_PERMISSION_CHEKE, (username, project_id))
        if not permission:
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        if export_type == 0:
            name = Sys_project.objects.get(id=project_id, is_delete=0).project_name
            file_name = name + "_项目报告导出_%s.xlsx" % time.strftime('%Y-%m-%d',time.localtime(time.time()))
            export_data, headers = export_report(project_id)
            if export_data and headers:
                # 操作记录日志
                object_desc = name + "(" + str(project_id) + ")"
                user_operate(username, "be_export_report", "ob_project", object_desc)
                return JsonResponse({'message': "导出成功", 'code': 200, 'file_name': file_name,
                                     'format': 'xlsx', 'headers': headers, 'data': export_data})
        if export_type == 1:
            name = Inte_task.objects.get(id=task_id, is_delete=0).task_name
            file_name = name + "_任务报告导出_%s.xlsx" % time.strftime('%Y-%m-%d',time.localtime(time.time()))
            export_data, headers = export_task_report(task_id)
            if export_data and headers:
                # 操作记录日志
                object_desc = name + "(" + str(project_id) + ")"
                user_operate(username, "be_export_report", "ob_project", object_desc)
                return JsonResponse({'message': "导出成功", 'code': 200, 'file_name': file_name,
                                     'format': 'xlsx', 'headers': headers, 'data': export_data})
        return JsonResponse({"message": "没有可以导出的报告", "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})

# 指定报告
def test_result(request, filename):
    try:
        return render(request, filename)
    except:
        return JsonResponse({"message": "报告不存在", "code": 500})


# 接口调试
@login_check
def request_test(request):
    username = request.session.get("username")
    if request.method == "POST":
        param_list, result_dict, msg = [], {}, 'ok'
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        case_id = params.get('case_id', '')
        task_case_id = params.get('task_case_id', '')

        if case_id or task_case_id:
            if case_id:  # 用例接口测试
                state, msg = params_secrect(params, ['req_method', 'project_id', 'req_path', 'case_id', 'subsystem_id'])
                if not state:
                    return JsonResponse({'message': msg, 'code': 500})
                # 根据用例id关联权限表
                case_id_permission = MySQLHelper().get_all(CASE_PERMISSION, (username, case_id))
                if not case_id_permission:
                    return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
                env_info = MySQLHelper().get_all(CASE_ENV_INFO, (case_id,))[0]
            else:  # 任务接口测试
                state, msg = params_secrect(params, ['req_method', 'req_path', 'task_case_id', 'project_id'])
                if not state:
                    return JsonResponse({'message': msg, 'code': 500})
                # 根据任务用例id关联权限表
                task_case_id_permission = MySQLHelper().get_all(TASK_CASE_PERMISSION, (username, task_case_id))
                if not task_case_id_permission:
                    return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
                env_info = MySQLHelper().get_all(TASK_ENV_INFO, (task_case_id,))[0]
            if env_info[1]:
                url = env_info[0] + ":" + env_info[1] + params.get("req_path", "")
            else:
                url = env_info[0] + params.get("req_path", "")
        else:  # 普通接口测试
            state, msg = params_secrect(params, ['env_id', 'req_method', 'project_id', 'subsystem_id'])
            if not state:
                return JsonResponse({'message': msg, 'code': 500})
            env_id = params.get('env_id', '')
            env_info = Sys_env.objects.filter(id=env_id, is_delete=0)
            if env_info[0].port:
                url = env_info[0].host + ":" + env_info[0].port + params.get("req_path", "")
            else:
                url = env_info[0].host + params.get("req_path", "")
        return request_test_operate(params, url, username)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 接口调试操作
def request_test_operate(params, url, username):
    """
    :param params: 请求参数
    :param url: 请求url
    :param username: 操作人
    :return:
    """
    method = params.get('req_method', '')
    param = params.get('req_param', '')
    headers = params.get('req_headers', '')
    project_id = params.get('project_id', '')
    subsystem_id = params.get('subsystem_id', '')
    req_body = convert_to_json(params.get('req_body')) if params.get('req_body', '') else ''
    req_file = params.get('req_file', '')
    extract_data, except_data, result, req_param_dict, recv_result = '', '', '', '', ''
    if type(param) == list:
        param = "".join([str(x) for x in param])
    try:
        extract_list = params.get('extract_list', '')
        except_list = params.get('except_list', '')
        result, req_param_dict, recv_result, code, global_variable, extract_data, except_data = interface_request(
            method, url, param, headers,
            req_body, req_file, project_id,
            subsystem_id,
            username, extract_list,
            except_list, is_single_interface=True)
        return JsonResponse({"code":200,"message":"请求成功","resp_result": result, "req_param_dict": req_param_dict, 'recv_result': recv_result,
                             'except_data': except_data, 'extract_data': extract_data, 'status_code': code})
    except Exception as e:
        return JsonResponse({"resp_result": result, "req_param_dict": req_param_dict, 'recv_result': recv_result,
                             'except_data': except_data, 'extract_data': extract_data, 'code': 500, 'message': str(e)})


# 文件上传
@login_check
def file_upload(request, id):
    if request.method == "POST":
        UPLOAD_PATH = 'static/upload'
        subsystem_name = Sys_subsystem.objects.filter(id=id).values("id")
        file_path = os.path.join(UPLOAD_PATH, str(subsystem_name[0]["id"]))
        if not os.path.exists(os.path.join(os.getcwd(), file_path)):
            os.makedirs(os.path.join(os.getcwd(), file_path))
        files_count = request.POST.get('files_count', '')
        print('file_count---------->%s' % files_count)
        filename_list = []
        for i in range(int(files_count)):
            resource_file = request.FILES['file' + str(i)]
            print(resource_file.name)
            destination = open(
                os.path.join(file_path, resource_file.name), 'wb+')
            for chunk in resource_file.chunks():
                destination.write(chunk)
            destination.close()
        return JsonResponse({"code": 200})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 任务管理列表
@login_check
def task_manager(request):
    if request.method == 'GET':
        pass
        # return render(request, 'task/task-list.html')
    elif request.method == "POST":
        username = request.session.get("username", "")
        param_list, result_dict, msg = [], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        task_name = param.get("task_name", '')
        project_id = param.get('project_id', 0)
        page = param.get("page", 1)
        limit = param.get("limit", 10)
        sql = TASK_LIST_LIKE % (username, task_name, project_id, project_id)
        task_list = MySQLHelper().get_all(sql)
        if page and limit:
            i = (int(page) - 1) * int(limit)
            j = (int(page) - 1) * int(limit) + int(limit)
            sub_task = task_list[i:j]
        else:
            sub_task = task_list
        total = len(task_list)
        sql_params = ['id', 'task_name', 'task_desc', 'cron', 'state',
                      'username', 'update_time', 'project_name', 'project_id',
                      'excel_file_name', 'creator', 'case_count']
        try:
            data = convert_data(sub_task, sql_params)
        except:
            msg = SERVER_ERROR
            data = []
        result_dict['code'] = 0
        result_dict['msg'] = msg if msg else ""
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 任务新增
@login_check
def task_add(request):
    username = request.session.get("username", "")
    if request.method == 'POST':
        # 任务添加
        param_list, result_dict, msg = ['task_name', 'project_id', 'cron'], {}, 'ok'
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        task_name = params.get('task_name', '')
        project_id = params.get('project_id', '')
        task_desc = params.get('task_desc', '')
        cron = params.get('cron', '')
        project_permission = MySQLHelper().get_all(PROJECT_PERMISSION_CHEKE, (username, project_id))
        if not project_permission:  # 根据项目id关联权限表
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        testtask = Inte_task.objects
        if Inte_task.objects.filter(is_delete=0, task_name=task_name, project_id=project_id):
            return JsonResponse({'message': '该任务名已存在', 'code': 500})
        if len(task_name) > 0 and len(cron) > 0:
            id = testtask.create(
                task_name=task_name,
                project_id=project_id,
                task_desc=task_desc,
                cron=cron,
                username=username,
                creator=username).id
            password = Sys_user_info.objects.get(username=username,is_delete=0).password
            try:
                email = Sys_user_info.objects.get(username=username, is_delete=0).email
                job_id, result = add_scheduler(task_name, username, password, cron, id, email)
                if result["msg"] == "Cron非法":
                    return JsonResponse({"message": "计划时间格式错误", "code": 500})
                if job_id == None:
                    Inte_task.objects.filter(id=id, is_delete=0).update(is_delete=1)
                    return JsonResponse({"message": "调度平台添加异常", "code": 500})
                testtask.filter(id=id,is_delete=0).update(job_id=job_id)
                context = {'message': ADD_SUCCESS_200, 'code': 200}
                object_desc = task_name + '(' + str(id) + ')'
                user_operate(username, "be_add", "ob_task", object_desc)  # 用户操作记录日志
                return JsonResponse(context)
            except:
                Inte_task.objects.filter(id=id,is_delete=0).update(is_delete=1)
                return JsonResponse({"message": "调度平台服务异常", "code": 500})
        else:
            context = {'message': ADD_FAIL_500, 'code': 500}
            return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 任务编辑
@login_check
def task_edit(request, id):
    username = request.session.get("username", '')
    project_permission = MySQLHelper().get_all(TASK_PERMISSION, (username, id))
    if not project_permission:  # 根据任务id关联权限表
        return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
    if request.method == 'GET':
        task_info_list = {}
        task_info = Inte_task.objects.get(is_delete=0, id=id)
        task_info_list['id'] = task_info.id
        task_info_list['task_name'] = task_info.task_name
        task_info_list['project_id'] = task_info.project_id
        task_info_list['task_desc'] = task_info.task_desc
        task_info_list['cron'] = task_info.cron
        return JsonResponse({'message': 'ok', 'code': 200, 'data': task_info_list})
    elif request.method == 'POST':
        param_list, result_dict, msg = ['task_name', 'project_id', 'cron'], {}, 'ok'
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        task_name = params.get('task_name', '')
        project_id = params.get('project_id', '')
        task_desc = params.get('task_desc', '')
        cron = params.get('cron', '')
        if int(id):
            exist = Inte_task.objects.filter(task_name=task_name, is_delete=0, project_id=project_id).exclude(id=id)
            if exist:
                return JsonResponse({'message': '该任务名已存在', 'code': 500})
            # if Inte_task.objects.filter(is_delete=0, id=id, project_id=project_id, state=1):
            #     return JsonResponse({'message': '修改任务请先停止任务', 'code': 500})
            testtask_info = Inte_task.objects.filter(id=id, is_delete=0)
            job_id = Inte_task.objects.get(id=id,is_delete=0).job_id
            try:
                testtask_info.update(
                    task_name=task_name,
                    project_id=project_id,
                    task_desc=task_desc,
                    cron=cron,
                    username=username,
                    update_time=get_time())
                result = edit_scheduler(job_id, cron, task_name, username)
                if result["msg"] == "Cron非法":
                    return JsonResponse({"message": "计划时间格式错误", "code": 500})
                context = {'message': EDIT_SUCCESS_200, 'code': 200}
                object_desc = task_name + '(' + str(id) + ')'
                user_operate(username, "be_edit", "ob_task", object_desc)  # 用户操作记录日志
            except Exception as e:
                print(e)
                context = {'message': EDIT_FAIL_500, 'code': 500}
            return JsonResponse(context)
        return JsonResponse({"message": NOT_ID, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 任务删除
@login_check
def task_delete(request):
    username = request.session.get('username', '')
    if request.method == 'POST':
        # 删除所有
        param_list, result_dict, msg = ["ids"], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get("ids")
        # 权限校验
        str_ids = ",".join(map(str, ids))  # 转换成 str 类型
        sql = DELETE_TASK_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        del_ids, del_list, task_name = [], [], []
        if type(ids) == list:
            sql = SELECT_TASK_EXTRACT_LIST % (str_ids, str_ids)
            # 任务用例表 extract_list
            extract_list = convert_data(MySQLHelper().get_all(sql), ["extract_list"])
            for dict in extract_list:
                for val in dict.values():
                    if val:
                        del_list.append(val)
            del_extract_list = ",".join(del_list).split(",")
            # 遍历任务表extract_list字段，查询用例表是否关联，关联则不删除
            for id in del_extract_list:
                sql = SELECT_CASE_EXTRACT_LIST % id
                case_list_exist = MySQLHelper().get_all(sql)
                if case_list_exist:
                    continue
                Inte_extract.objects.filter(id=id).update(is_delete=1)
            # 更新任务表与任务用例表is_delete
            for id in ids:
                name = Inte_task.objects.get(id=id).task_name
                if Inte_report.objects.filter(task_id=id, is_delete=0):
                    continue
                if Inte_task_case.objects.filter(task_id=id, is_delete=0):
                    continue
                ret = Inte_task.objects.filter(id=id, is_delete=0, state=0)
                if ret:
                    job_id = Inte_task.objects.get(id=id).job_id
                    if job_id:
                        del_scheduler(job_id)
                    ret.update(is_delete=1, username=username)
                    del_ids.append(id)
                    task_name.append(name)
            if len(ids) == len(del_ids):
                object_desc = ",".join(map(str, task_name)) + '(' + str_ids + ')'
                user_operate(username, "be_del", "ob_task", object_desc)  # 用户操作记录日志
                return JsonResponse({'message': DEL_SUCCESSS_200, 'code': 200})
            else:
                if len(del_ids) < 1:
                    for id in ids:
                        if Inte_report.objects.filter(task_id=id, is_delete=0):
                            return JsonResponse({"message": "该任务下有报告，请先删除报告", "code": 500})
                        if Inte_task_case.objects.filter(task_id=id, is_delete=0):
                            return JsonResponse({"message": "该任务已勾选用例，请先取消勾选", "code": 500})
                return JsonResponse({'message': "成功删除%s条" % len(del_ids), 'code': 200})
        return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 任务接口管理
@login_check
def task_case_manager(request, scoure=None):
    username = request.session.get("username", '')
    if request.method == "GET":
        pass
        # return render(request, 'task/task-case-list.html')
    elif request.method == "POST":
        param_list, result_dict, msg = ["task_id"], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        if scoure == "tree":
            # 任务模块用例树形图
            state, msg = params_secrect(param, ['subsystem_id'])
            if not state:
                return JsonResponse({'message': msg, 'code': 500})
            subsystem_id = param.get("subsystem_id", "")
            task_id = param.get("task_id", "")
            module_list = Sys_module.objects.filter(subsystem_id=subsystem_id, is_delete=0)
            module_list_str = ','.join([module.case_list for module in module_list if module.case_list]).strip(
                ',') if module_list else ''
            # 用例查询sql语句
            if module_list_str:
                sql = CASE_LIST % (module_list_str, module_list_str)
                case_info = MySQLHelper().get_all(sql)
            else:
                case_info = ()
            ret = MySQLHelper().get_all(MODULE_LIST_TREE, (username, subsystem_id))
            # 用例根节点
            path_ret = MySQLHelper().get_all(MODULE_PATH, (subsystem_id,))
            path = path_ret[0][0] if path_ret else ""
            if not ret:
                return JsonResponse({'data': [{"title": path,"id": subsystem_id,'level': 0}],}, safe=False)
            ret = convert_data(ret + case_info, ['id', 'title', 'parent_id', 'level', 'report_path', 'module_type'])
            result = list_to_tree(ret)
            all_result = [{"title": path, "id": subsystem_id,"children": result, 'level': 0, 'spread': True}]
            check_data = ''
            task_info = Inte_task.objects.filter(id=task_id, is_delete=0)
            if task_info:
                check_data = json.loads(task_info[0].case_dict).get(str(subsystem_id), '').split(',') if task_info[
                    0].case_dict else ''
                if check_data == ['']:
                    check_data = []
            return JsonResponse({"code": 0,'data': all_result, 'check_data': check_data}, safe=False)
        elif scoure == "table":
            page = param.get("page", 1)
            limit = param.get("limit", 10)
            module_id = param.get('module_id', '')
            detail = param.get('detail', '')
            task_id = param.get('task_id', '')
            subsystem_id = param.get('subsystem_id', '')
            state_choose = param.get('state', 2)
            type_choose = param.get('case_type', 0)
            # 指定系统的任务用例
            task_case_list = Inte_task.objects.filter(id=task_id, is_delete=0)
            if subsystem_id or module_id:
                # 指定版本的任务用例
                task_case_dict = task_case_list[0].case_dict if task_case_list else ''
                task_case_dict = json.loads(task_case_dict) if task_case_dict else ''
                task_case_list = task_case_dict.get(str(subsystem_id)) if task_case_dict else ''
                # 指定模块的任务用例列表
                if module_id:
                    module_case_list = Sys_module.objects.filter(id=module_id, is_delete=0)
                    case_list = module_case_list[0].case_list.split(',') if module_case_list else []
                    task_case_list = ','.join([x for x in task_case_list.split(',') if x in case_list])
                    task_case_list = task_case_list if task_case_list else ''
            # 全部任务用例
            else:
                task_case_list = ','.join([x for x in list(eval(task_case_list[0].case_list).values()) if x]).strip(
                    ',') if task_case_list[
                    0].case_list else ''
            if task_case_list:
                sql = TASK_CASE_LIST % (
                    int(task_id), task_case_list, type_choose, type_choose, detail, state_choose, state_choose,
                    task_case_list)
                case_detail = MySQLHelper().get_all(sql)
                total = len(case_detail)
                if total > 10:
                    i = (int(page) - 1) * int(limit)
                    j = (int(page) - 1) * int(limit) + int(limit)
                    sub_task_interface = case_detail[i:j]
                else:
                    sub_task_interface = case_detail
                sql_params = [
                    'id', 'case_id', 'case_name', 'req_path',
                    'req_method', 'extract_list', 'state', 'subsystem_id', 'case_type'
                ]
                data = convert_data(sub_task_interface, sql_params)
            else:
                total = 0
                data = []
            result_dict['code'] = 0
            result_dict['msg'] = ""
            result_dict['count'] = total
            result_dict['data'] = data
            return JsonResponse(result_dict, safe=False)
        return JsonResponse({"message": NOT_METHMOD, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


def handle_task_case(task_id, old_case_list, old_subsystem_list, recv_list, username):
    # case_list 字段存储的各个类型的用例在当前子系统的用例
    old_case_list = old_case_list.split(',') if old_case_list else []
    old_subsystem_case_list = [x for x in old_case_list if x in old_subsystem_list]

    # 未在新增用例列表中需要删除的用例
    case_del = [x for x in old_subsystem_case_list if x not in recv_list]
    Inte_task_case.objects.filter(task_id=task_id, case_id__in=case_del).update(is_delete=1, username=username,
                                                                                update_time=get_time())
    # 保留在新增用例中的已存在的用例
    case_old = [x for x in old_subsystem_case_list if x in recv_list]
    # 新添加的部分用例
    add_new_list = [y for y in recv_list if y not in case_old]
    # case_list 字段中剔除已删除的用例id添加新增的用例id
    new_case_list = [x for x in old_case_list if x not in case_del] + add_new_list
    # 子系统的用例集
    new_subsystem_list = case_old + add_new_list
    return new_case_list, add_new_list, new_subsystem_list


# 任务接口新增
@login_check
def task_case_add(request, task_id):
    username = request.session.get("username", "")
    project_permission = MySQLHelper().get_all(TASK_PERMISSION, (username, task_id))
    if not project_permission:  # 根据任务id关联权限表
        return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
    if request.method == "POST":
        # 新增接口
        param_list, result_dict, msg = ['data', 'subsystem_id'], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        # 接收到的某个版本的用例列表
        recv_case = param.get('data', '')
        subsystem_id = param.get('subsystem_id', '')

        if type(recv_case) != dict:
            return JsonResponse({"code": 500, "message": "data类型不是dict"})
        task_info = Inte_task.objects.filter(id=task_id)
        if not task_info:
            return JsonResponse({"code": 500, "message": TASK_NOT_FOUND})
        if Inte_task.objects.filter(id=task_id, is_delete=0, state=1):
            return JsonResponse({"code": 500, "message": "任务运行中，禁止操作"})

        task_case_dict = task_info[0].case_dict
        old_dict_case = ''
        # 获取当前系统的所有用例id
        if task_case_dict:
            case_dict = json.loads(task_case_dict)
            if case_dict.get(str(subsystem_id)):
                old_dict_case = case_dict.get(str(subsystem_id))
        old_subsystem_list = old_dict_case.split(',') if old_dict_case else []
        # 任务的所有用例id
        recv_case_list = list(recv_case.values())
        old_case_list = [x for x in list(eval(task_info[0].case_list).values())] if task_info[0].case_list else ['', '',
                                                                                                                 '']
        case_str, new_case, create_list = '', '', []

        # 前置条件用例集
        new_before_all_list, new_before_add_case, new_before_subsystem_list = handle_task_case(task_id,
                                                                                               old_case_list[0],
                                                                                               old_subsystem_list,
                                                                                               recv_case_list[0],
                                                                                               username)

        # 普通用例集
        new_case_all_list, new_case_add_case, new_case_subsystem_list = handle_task_case(task_id, old_case_list[1],
                                                                                         old_subsystem_list,
                                                                                         recv_case_list[1], username)
        # 后置条件用例集
        new_after_all_list, new_after_add_case, new_after_subsystem_list = handle_task_case(task_id, old_case_list[2],
                                                                                            old_subsystem_list,
                                                                                            recv_case_list[2], username)
        new_case = new_before_add_case + new_case_add_case + new_after_add_case
        new_case = (','.join([x for x in new_case if x])).strip(',')
        all_case_str = new_before_subsystem_list + new_case_subsystem_list + new_after_subsystem_list
        all_case_str = (','.join([x for x in all_case_str if x])).strip(',')
        if new_case:
            sql = TASK_CASE_ADD_LIST % (new_case, new_case)
            interface_detail = MySQLHelper().get_all(sql)
            sql_params = [
                'case_id', 'case_name', 'req_path', 'req_method', 'req_headers', 'req_param',
                'req_body', 'req_file', 'extract_list', 'except_list', 'run_time', 'wait_time', 'env_id', 'state'
            ]
            task_interface_data = convert_data(interface_detail, sql_params)
            for data in task_interface_data:
                create_list.append(
                    Inte_task_case(task_id=task_id, case_id=data['case_id'], case_name=data['case_name'],
                                   req_path=data['req_path'], req_method=data['req_method'],
                                   req_headers=data['req_headers'], req_param=data['req_param'],
                                   req_body=data['req_body'],
                                   req_file=data['req_file'], extract_list=data['extract_list'],
                                   except_list=data['except_list'], username=username, run_time=data['run_time'],
                                   wait_time=data['wait_time'], env_id=data['env_id'], state=data['state']))
        try:

            user_operate(username, "be_add", "ob_task_case", new_case)  # 用户操作记录日志
            Inte_task_case.objects.bulk_create(create_list)
        except Exception as e:
            print(e)
            return JsonResponse({'message': ADD_FAIL_500, 'code': 500})
        try:
            if not task_case_dict:
                case_dict = {}
                case_dict[subsystem_id] = all_case_str
                case_dict = json.dumps(case_dict)
            else:
                case_dict = json.loads(task_case_dict)
                if all_case_str:
                    case_dict[subsystem_id] = all_case_str
                else:
                    del case_dict[subsystem_id]
                case_dict = json.dumps(case_dict)
            save_list = json.dumps(
                {"before_list": (','.join(new_before_all_list)).strip(','),
                 "task_list": (','.join(new_case_all_list)).strip(','),
                 "after_list": (','.join(new_after_all_list)).strip(',')
                 })
            task_info.update(case_list=save_list, case_dict=case_dict, username=username,
                             update_time=get_time())
            context = {'message': ADD_SUCCESS_200, 'code': 200}
        except Exception as e:
            print(e)
            context = {'message': ADD_FAIL_500, 'code': 500}
        return JsonResponse(context)


# 任务接口编辑
@login_check
def task_case_edit(request, id):
    username = request.session.get("username", "")
    if request.method == 'GET':
        task_case_params = [
            'id', 'interface_name', 'case_name', 'req_path',
            'req_method', 'req_headers', 'req_param', 'req_body', 'req_file',
            'extract_list', 'except_list', 'run_time', 'wait_time'
        ]
        task_id = request.GET.get("task_id")
        if not task_id:
            # 列表任务用例详情
            task_case_info = convert_one_to_many_data(MySQLHelper().get_all(SELECT_TASK_CASE_INFO,
                                                                            (username, id)), task_case_params, 1)
            case_type = 'task'
        else:
            # 左侧树形图点击用例详情
            task_case_info = convert_one_to_many_data(MySQLHelper().get_all(SELECT_TASK_CASE_INFO_TREE,
                                                                            (username, id, task_id)), task_case_params,
                                                      1)
            case_type = 'task'

            # 未添加进任务的用例详情
            if not task_case_info:
                task_case_info = convert_one_to_many_data(MySQLHelper().get_all(TASK_CASE_INFO,
                                                                                (username, id)), task_case_params, 1)
                case_type = 'case'
        data = task_case_info[0] if task_case_info else []
        return JsonResponse({'message': 'ok', 'code': 200, 'data': data, 'case_type': case_type})
    elif request.method == 'POST':
        param_list, msg = ['project_id', 'case_name', 'req_path', 'req_method', 'run_time', 'wait_time'], 'ok'
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        project_id = params.get('project_id', '')
        subsystem_id = params.get('subsystem_id', '')
        case_name = params.get('case_name', '')
        req_path = params.get('req_path', '')
        req_headers = convert_to_json(params.get('req_headers')) if params.get('req_headers', '') else ''
        req_param = convert_to_json(params.get('req_param')) if params.get('req_param', '') else ''
        req_body = convert_to_json(params.get('req_body')) if params.get('req_body', '') else ''
        req_file = json.dumps(params.get('req_file'), ensure_ascii=False) if params.get('req_file', '') else ''
        req_method = params.get('req_method', '')
        run_time = params.get('run_time', 1)
        wait_time = params.get('wait_time', 0)
        extract_list = params.get('extract_list', '')
        except_list = params.get('except_list', '')
        update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        project_permission = MySQLHelper().get_all(GET_PERSON_PROJECT, (username, project_id))
        if project_permission:
            if int(id):
                inte_extract_info = Inte_extract.objects
                extract_id, create_list, extract_name_list, update_objs, new_extract_id, old_extract_id \
                    = '', [], [], [], [], []
                if extract_list:
                    for rule_dict in extract_list:
                        extract_name = rule_dict['name']
                        extract_rule = rule_dict['rule']
                        data_format = rule_dict['dataFormat']
                        if "id" in rule_dict.keys():
                            update_info = inte_extract_info.filter(id=rule_dict['id'])[0]
                            if update_info:
                                update_info.param_name = extract_name
                                update_info.rule = extract_rule
                                update_info.data_format = data_format
                                update_objs.append(update_info)
                        else:
                            create_list.append(
                                Inte_extract(param_name=extract_name, rule=extract_rule, data_format=data_format,
                                             project_id=project_id, username=username))
                        extract_name_list.append(extract_name)
                    try:
                        bulk_update(update_objs)
                    except Exception as e:
                        print(e)
                        return JsonResponse({'message': EXTRACT_NAME_REPRTITION, 'code': 500})
                    if create_list:
                        try:
                            Inte_extract.objects.bulk_create(create_list)
                        except Exception as e:
                            print(e)
                            return JsonResponse({'message': EXTRACT_NAME_REPRTITION, 'code': 500})

                    id_result = MySQLHelper().get_all(SELECT_EXTRACT_ID, (project_id, tuple(extract_name_list)))
                    extract_id = ",".join([str(x[0]) for x in id_result])

                    new_extract_id = extract_id.split(",")
                task_case_info = Inte_task_case.objects.filter(id=id, is_delete=0)
                old_extract_id = task_case_info[0].extract_list.split(',') if task_case_info[
                    0].extract_list else []
                del_list = [del_old_id for del_old_id in old_extract_id if del_old_id not in new_extract_id]
                inte_extract_info.filter(id__in=del_list).delete()
                task_case_info.update(
                    case_name=case_name,
                    req_path=req_path,
                    req_headers=req_headers,
                    req_param=req_param,
                    req_body=req_body,
                    req_file=req_file,
                    username=username,
                    req_method=req_method,
                    extract_list=extract_id,
                    except_list=except_list,
                    run_time=run_time,
                    wait_time=wait_time,
                    update_time=update_time)
                object_desc = case_name + '(' + str(id) + ')'
                user_operate(username, "be_edit", "ob_task_case", object_desc)  # 用户操作记录日志
                context = {'message': EDIT_SUCCESS_200, 'code': 200}
            else:
                context = {'message': EDIT_FAIL_500, 'code': 500}
        else:
            context = {'message': NOT_PERMISSION, 'code': 500}
    return JsonResponse(context)


# 任务接口删除
@login_check
def task_case_delete(request):
    username = request.session.get("username", "")
    if request.method == 'POST':
        param_list, result_dict, msg = ["ids", "task_id"], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get("ids")
        task_id = param.get("task_id")
        # 权限校验
        map_ids = map(str, ids)  # 格式化
        str_ids = ",".join(map_ids)  # 转换成 str 类型
        sql = DELETE_TASK_CASE_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        task_info = Inte_task.objects.filter(id=task_id, is_delete=0)
        if not task_info:
            return JsonResponse({'message': "当前任务不存在", 'code': 500})
        task_info = task_info[0]
        if_dict = eval(Inte_task.objects.get(id=task_id).case_list)
        case_dict = json.loads(task_info.case_dict) if task_info.case_dict else ''
        if type(ids) == list:
            case_id_list = []
            for id in ids:
                del_id = Inte_task_case.objects.filter(id=id, is_delete=0)
                case_id_list.append(del_id[0].case_id)
                del_id.update(is_delete=1, username=username, update_time=get_time())
            for key, value in if_dict.items():
                if value:
                    value = ','.join(map(str, [int(x) for x in value.split(',') if int(x) not in case_id_list]))
                if_dict[key] = value
            for key, value in case_dict.items():
                if value:
                    value = ','.join(map(str, [int(x) for x in value.split(',') if int(x) not in case_id_list]))
                case_dict[key] = value
            if_dict = json.dumps(if_dict) if if_dict else ''
            case_dict = json.dumps(case_dict) if case_dict else ''
            Inte_task.objects.filter(id=task_id).update(case_list=if_dict, case_dict=case_dict, username=username,
                                                        update_time=get_time())
            context = {'message': DEL_SUCCESSS_200, 'code': 200}
            user_operate(username, "be_del", "ob_task_case", str_ids)  # 用户操作记录日志
            return JsonResponse(context)
        return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 任务接口上下顺序移动
@login_check
def task_case_upAndDown(request):
    username = request.session.get("username", "")
    if request.method == 'POST':
        param_list = ['task_id', 'if_id', 'mode']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        task_id = param.get("task_id")
        if_id = param.get("if_id")
        mode = param.get("mode")
        if_id_str = (",".join(map(str, if_id))).strip(',')  # # list -- str
        if type(if_id) != list or not if_id:
            return JsonResponse({'message': 'if_id' + NOT_LIST, 'code': 200})
        project_permission = MySQLHelper().get_all(TASK_PERMISSION, (username, task_id))
        if not project_permission:  # 根据任务id关联权限表
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        case_list = eval(Inte_task.objects.get(id=task_id, is_delete=0).case_list)
        # 更新case_list 字段
        for key in case_list:
            case_str = case_list[key]
            if if_id_str not in case_str:
                continue
            if_list_up = case_str.split(',')  # str -- list
            if mode == "up":  # 上移
                try:
                    if str(if_id[0]) == if_list_up[0]:
                        return JsonResponse({'message': "当前范围已经是最前一条了", 'code': 500})
                    for i in if_id:
                        if_index = if_list_up.index(str(i))
                        if_list_up[if_index - 1], if_list_up[if_index] = if_list_up[if_index], if_list_up[if_index - 1]
                    if_result = (",".join(str(i) for i in if_list_up))
                    case_list[key] = if_result
                    Inte_task.objects.filter(id=task_id).update(case_list=case_list)
                    object_desc = "移动ID:" + if_id_str + ",移动后位置:" + if_result
                    user_operate(username, "be_up", "ob_task_case", object_desc)  # 用户操作记录日志
                    context = {'message': MOVE_SUCCESS_200, 'code': 200}
                except Exception as e:
                    print(e)
                    context = {'message': MOVE_FAIL_500, 'code': 500}
                return JsonResponse(context)
            elif mode == "down":  # 下移
                try:
                    len_if_id = len(if_id)
                    if str(if_id[-1]) == if_list_up[-1]:
                        return JsonResponse({'message': "当前范围已经是最后一条了", 'code': 500})
                    for i in if_id:
                        if_index = if_list_up.index(str(i))
                        if_list_up[if_index], if_list_up[if_index + len_if_id] = if_list_up[if_index + len_if_id], \
                                                                                 if_list_up[if_index]
                        len_if_id -= 1
                    if_result = (",".join(str(i) for i in if_list_up))
                    case_list[key] = if_result
                    Inte_task.objects.filter(id=task_id).update(case_list=case_list)
                    object_desc = "移动ID:" + if_id_str + ",移动后位置:" + if_result
                    user_operate(username, "be_down", "ob_task_case", object_desc)  # 用户操作记录日志
                    context = {'message': MOVE_SUCCESS_200, 'code': 200}
                except Exception as e:
                    print(e)
                    context = {'message': MOVE_FAIL_500, 'code': 500}
                return JsonResponse(context)
            else:
                return JsonResponse({"message": "mode值错误！", "code": 500})
        return JsonResponse({"message": "只能移动范围内且相邻的用例！", "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 执行任务
@login_check
def execute_tasks(request, id):
    if request.method == "POST":
        param_list, result_dict, msg = ["source"], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        username = request.session.get("username", '')
        source = param.get("source")
        try:
            task_info = Inte_task.objects.get(id=id)
        except:
            return JsonResponse({"code": 500, "message": TASK_NOT_FOUND})
        task_list = task_info.case_list
        if not task_list:
            return JsonResponse({"message": TASK_IS_EMPTY, "code": 500})
        task_list = (','.join([x for x in list(eval(task_list).values()) if x])).strip(',')
        if not task_list:
            return JsonResponse({"message": TASK_IS_EMPTY, "code": 500})
        subsystem_dict = list(eval(task_info.case_dict).keys())
        interface_count = len(Inte_interface.objects.filter(subsystem_id__in=subsystem_dict, is_delete=0, state=1))
        crons = task_info.cron
        sql = EXECTUE_TASK % (interface_count, username, id, task_list, task_list)
        sql_result = MySQLHelper().get_all(sql)
        sql_params = [
            'id', 'case_name', 'module_id', 'module_name', 'host', 'port', 'req_method', 'req_path', 'req_headers',
            'req_param', 'req_body', 'req_file', 'extract_list', 'except_list', 'interface_count', 'subsystem_id',
            'run_time', 'wait_time', 'module_type', 'interface_id', 'project_id', 'type'
        ]
        task_data = convert_one_to_many_data(sql_result, sql_params, False)
        task_detail = convert_runtime(task_data)
        # 执行测试任务
        return runTask(task_detail, id, source, username, task_info.task_name, task_info.project_id)

# 执行任务
def runTask(task_detail, task_id, source, username, report_name, project_id):
    """
    :param task_detail: 任务详情
    :param task_runtime: 任务执行时间
    :param task_id: 任务id
    :param source: 执行方式
    :param username: 操作人
    :param report_name: 任务名称
    :param project_id: 项目id
    :return:
    """
    if source == 'once':
        try:
            # response, _ = threading.Thread(target=Test.test_suite(task_detail, "task", task_id, username, report_name, project_id))
            # response.start()
            response, result_file = Test.test_suite(task_detail, "task", task_id, username, report_name, project_id)
            object_desc = report_name + '(' + str(task_id) + ')'
            user_operate(username, "be_now_run", "ob_task", object_desc)  # 用户操作记录日志
            task_desc = None
            for res_data in response:
                if '失败' == res_data[5]:
                    break
            else:
                task_desc = 1
            if task_desc:
                context = {"message": EXECUTE_CASE_SUCCESS, "code": 200}
            else:
                context = {"message": EXECUTE_CASE_FAIL, "code": 500}
        except BaseException as e:
            context = {
                "message": EXECUTE_CASE_EXCEPT % str(e),
                "code": "500"
            }
    else:
        try:
            job_id = Inte_task.objects.get(id=task_id, is_delete=0).job_id
            start_scheduler(job_id)
            Inte_task.objects.filter(id=task_id).update(state=1)
            object_desc = report_name + '(' + str(task_id) + ')'
            user_operate(username, "be_plan_run", "ob_task", object_desc)  # 用户操作记录日志
            context = {'message': RUN_TASK_SUCCESS_200, 'code': 200}
        except Exception as e:
            print(e)
            context = {'message': RUN_TASK_FAIL_500, 'code': 500}
    return JsonResponse(context)


# 任务停止
@login_check
def stop_tasks(request, id):
    if request.method == "GET":
        try:
            username = request.session.get("username", "")
            job_id = Inte_task.objects.get(id=id,is_delete=0).job_id
            stop_scheduler(job_id)
            Inte_task.objects.filter(id=id).update(state=0)
            task_name = Inte_task.objects.get(id=id).task_name
            object_desc = task_name + '(' + str(id) + ')'
            user_operate(username, "be_stop_run", "ob_task", object_desc)  # 用户操作记录日志
            context = {'message': STOP_TASK_SUCCESS_200, 'code': 200}
        except Exception as e:
            print(e)
            context = {'message': STOP_TASK_FAIL_500, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})

# 任务报告
@login_check
def task_report(request):
    if request.method == "POST":
        state, param = params_check(request.body, ['id'])
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        id = param.get('id', '')
        page = param.get('page', 1)
        rows = param.get("limit", 10)
        i = (int(page) - 1) * int(rows)
        j = (int(page) - 1) * int(rows) + int(rows)
        report_list = MySQLHelper().get_all(TASK_REPORT_LIST, (id,))
        sql_params = ['id', 'task_name', 'report_path', 'file_name', 'report_type', 'update_time', 'username']
        sub_report = report_list[i:j]
        data = convert_data(sub_report, sql_params)
        total = len(report_list)
        result_dict = {}
        result_dict['code'] = 0
        result_dict['msg'] = ""
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


@login_check
def mock_server(request, router, path):
    try:
        mockList = Sys_mock_server.objects.get(
            mock_router=router, mock_path=path, mock_state=1)
        result = eval(mockList.mock_json)
        print(result)
        return JsonResponse(
            result, safe=False, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        print(e)
        return JsonResponse(
            DATA_NOT_FOUND,
            safe=False,
            json_dumps_params={'ensure_ascii': False})


# 参数管理
@login_check
def param_manager(request):
    username = request.session.get("username", "")
    if request.method == "POST":
        param_list, result_dict, msg = ["project_id"], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        param_name = param.get('param_name', '')
        project_id = param.get("project_id", '')
        page = param.get('page', 1)
        limit = param.get("limit", 10)
        # 检验参数
        sql = PARAM_LIST_LIKE % (username, param_name, project_id)
        param_list = MySQLHelper().get_all(sql)
        total = len(param_list)
        if total > 10:
            i = (int(page) - 1) * int(limit)
            j = (int(page) - 1) * int(limit) + int(limit)
            sub_param = param_list[i:j]
        else:
            sub_param = param_list
        sql_params = [
            'id', 'param_name', 'param_desc', 'rule', 'rule_name',
            'input_params', 'update_time', 'username'
        ]
        data = convert_data(sub_param, sql_params)
        result_dict['code'] = 0
        result_dict['msg'] = msg if msg else ""
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 获取参数列表

def param_rule_list(request):
    if request.method == 'GET':
        param_list = MySQLHelper().get_all(
            """select id, dict_key, dict_value, if_param from `sys_dict` where dict_type=1""")
        sql_params = ['id', 'dict_key', 'dict_value', 'if_param']
        rule_data = convert_data(param_list, sql_params)
        for i in rule_data:
            i['annotation'] = eval(i['dict_key']).__doc__
        context = {'code': 200,'data': rule_data }
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 自定义变量测试
@login_check
def param_test(request):
    if request.method == 'POST':
        param_list, result_dict, msg = ["param_rule"], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        # project_id = param.get('project_id', '')
        param_rule = param.get('param_rule', '') # 参数规则，取参数列表中的id
        input_params = param.get('input_params', '') #函数参数
        try:
            param_result = convert_customparam_test(param_rule, input_params)
            return JsonResponse({'code': 200, 'result': param_result, 'message': PARAM_NAME_GENERATOR_SUCCESS})
        except Exception as e:
            return JsonResponse({'code': 500, 'message': PARAM_NAME_GENERATOR_FAIL + ',' + str(e)})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 自定义参数新增
@login_check
def param_add(request):
    username = request.session.get("username", "")
    if request.method == 'POST':
        param_list, result_dict, msg = ["project_id", "param_rule", "param_name"], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        param_name = param.get('param_name', '')
        param_desc = param.get('param_desc', '')
        rule = param.get('param_rule', '')
        input_params = param.get('input_params', '')
        project_id = param.get('project_id', '')
        param_list = Sys_public_param.objects
        project_permission = MySQLHelper().get_all(PROJECT_PERMISSION_CHEKE, (username, project_id))
        if not project_permission:
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        if Sys_public_param.objects.filter(is_delete=0, param_name=param_name, project_id=project_id):
            return JsonResponse({'message': "该参数名已存在", 'code': 500})
        if len(param_name) > 0:
            object_id = param_list.create(
                param_name=param_name,
                param_desc=param_desc,
                rule=rule,
                input_params=input_params,
                project_id=project_id,
                username=username,
                param_type=2).id
            object_desc = param_name + '(' + str(object_id) + ')'
            user_operate(username, "be_add", "ob_variate", object_desc)  # 用户操作记录日志
            context = {'message': ADD_SUCCESS_200, 'code': 200}
        else:
            context = {'message': ADD_FAIL_500, 'code': 200}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 参数编辑
def param_edit(request, id):
    username = request.session.get("username", "")
    project_permission = MySQLHelper().get_all(PARAM_PERMISSION, (username, id))
    if not project_permission:  # 根据参数id关联权限表
        return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
    if request.method == 'GET':
        param_list = MySQLHelper().get_all(PARAM_INFO, (id,))
        sql_param = [
            'id', 'param_name', 'param_desc', 'param_rule', 'input_params', 'project_id']
        param_data = convert_data(param_list, sql_param)
        content = {'code': 200, 'param_data': param_data[0]}
        return JsonResponse(content)
    elif request.method == 'POST':
        param_list, result_dict, msg = ["project_id", "param_rule", "param_name"], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        param_name = param.get('param_name', '')
        param_desc = param.get('param_desc', '')
        param_rule = param.get('param_rule', '')
        input_params = param.get('input_params', '')
        project_id = param.get('project_id', '')
        if int(id):
            exist = Sys_public_param.objects.filter(param_name=param_name, is_delete=0, project_id=project_id).exclude(
                id=id)
            if exist:
                return JsonResponse({'message': "该参数名已存在", 'code': 500})
            param_info = Sys_public_param.objects.filter(id=id, is_delete=0)
            try:
                param_info.update(
                    param_name=param_name,
                    param_desc=param_desc,
                    rule=param_rule,
                    input_params=input_params,
                    project_id=project_id,
                    update_time=get_time(),
                    username=username)
                object_desc = param_name + '(' + str(id) + ')'
                user_operate(username, "be_edit", "ob_variate", object_desc)  # 用户操作记录日志
                context = {'message': EDIT_SUCCESS_200, 'code': 200}
            except Exception as e:
                print(e)
                context = {'message': EDIT_FAIL_500, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 参数删除
@login_check
def param_delete(request):
    username = request.session.get("username", "")
    if request.method == 'POST':
        # 删除所有
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get("ids")
        # 权限校验
        map_ids = map(str, ids)  # 格式化
        str_ids = ",".join(map_ids)  # 转换成 str 类型
        sql = DELETE_PARAM_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        if type(ids) == list:
            del_ids = []
            param_name = []
            for id in ids:
                name = Sys_public_param.objects.get(id=id).param_name
                param = Sys_public_param.objects.filter(id=id, is_delete=0)
                if len(param) != 0:
                    param.update(is_delete=1, username=username, update_time=get_time())
                    # param.delete()
                    del_ids.append(id)
                    param_name.append(name)
            if len(ids) == len(del_ids):
                object_desc = ",".join(map(str, param_name)) + '(' + str_ids + ')'
                user_operate(username, "be_del", "ob_variate", object_desc)  # 用户操作记录日志
                context = {'message': DEL_SUCCESSS_200, 'code': 200}
            else:
                context = {'message': DEL_FAIL_500, 'code': 500}
            return JsonResponse(context)
        return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 子系统列表管理
@login_check
def subsystem_manager(request, project_id):
    username = request.session.get("username", "")
    if request.method == "POST":
        param_list, result_dict, msg = [], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({"message": param, "code": 0})
        page = param.get("page", '')  # 分页
        limit = param.get("limit", '')  # 数量
        subsystem_name = param.get("subsystem_name", "")
        try:
            project_id = int(project_id)
        except:
            return JsonResponse({"message": PROJECT_NOT_FOUND, "code": 500})
        # 检验参数
        sql = SUBSYSTEM_LIST_LIKE % (username, subsystem_name, project_id)
        subsystem_list = MySQLHelper().get_all(sql)
        if page and limit:  #
            i = (int(page) - 1) * int(limit)
            j = (int(page) - 1) * int(limit) + int(limit)
            sub_project = subsystem_list[i:j]
        else:
            sub_project = subsystem_list
        total = len(subsystem_list)
        sql_params = ['id', 'subsystem_name', 'subsystem_desc']
        try:
            data = convert_data(sub_project, sql_params)
        except Exception as e:
            print(e)
            msg = SERVER_ERROR
            data = []
        result_dict['code'] = 0
        result_dict['msg'] = msg if msg else ""
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 子系统新增
@login_check
def subsystem_add(request):
    if request.method == "POST":
        subsystem_list = ["subsystem_name", "project_id"]
        state, param = params_check(request.body, subsystem_list)
        if not state:  # 没有传body
            return JsonResponse({"message": param, "code": 500})
        subsystem_name = param.get("subsystem_name", "")  # 前端传进来的subsystem_name
        subsystem_desc = param.get("subsystem_desc", "")  # 前端传进来的subsystem_desc
        project_id = param.get("project_id", "")  # 前端传进来的project_id
        username = request.session.get("username", "")  # 从session获取username
        project_permission = MySQLHelper().get_all(PROJECT_PERMISSION_CHEKE, (username, project_id))
        if not project_permission:  # 校验权限
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        if len(subsystem_name) > 18:
            return JsonResponse({"message": "系统名称输入超长！", "code": 500})
        if len(subsystem_desc) > 200:
            return JsonResponse({"message": "系统说明输入超长！", "code": 500})
        subsystem_exist = Sys_subsystem.objects.filter(subsystem_name=subsystem_name, is_delete=0,
                                                       project_id=project_id)  # 新增的名称已存在
        if subsystem_exist:
            return JsonResponse({"message": NAME_REPETITION, "code": 500})  # 名称重复，抛异常
        project_id_exist = Sys_project.objects.filter(id=project_id)
        if project_id_exist:  # 判断前端传进来的项目id存在数据库
            if subsystem_name:
                # 往系统表写入数据
                subsystem_id = Sys_subsystem.objects.create(subsystem_name=subsystem_name,
                                                            subsystem_desc=subsystem_desc,
                                                            username=username, project_id=project_id).id
                # 往用户权限表写入数据
                Sys_module.objects.create(module_name='前置条件', username=username, module_type=2,
                                          subsystem_id=subsystem_id)
                Sys_module.objects.create(module_name='后置条件', username=username, module_type=3,
                                          subsystem_id=subsystem_id)
                object_desc = subsystem_name + '(' + str(subsystem_id) + ')'
                user_operate(username, "be_add", "ob_subsystem", object_desc)  # 用户操作记录日志
                context = {"message": ADD_SUCCESS_200, "code": 200}  # 添加成功
            else:
                context = {"message": ADD_FAIL_500, "code": 500}  # 添加失败，抛异常
            return JsonResponse(context)
        return JsonResponse({"message": PROJECT_NOT_FOUND, "code": 500})  # 项目不存在，抛异常
    return JsonResponse({"message": NOT_METHMOD, "code": 500})  # 请求不存在，抛异常


# 子系统编辑
@login_check
def subsystem_edit(request, id):
    username = request.session.get("username", "")
    subsystem_obj = Sys_subsystem.objects
    project_permission = MySQLHelper().get_all(SUBSYSTEM_OPERATE, (username, id))
    if not project_permission:  # 校验权限
        return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
    if request.method == "GET":
        info = subsystem_obj.get(id=id, is_delete=0)
        data = {'id': id, 'subsystem_name': info.subsystem_name, 'subsystem_desc': info.subsystem_desc,
                'project_id': info.project_id}
        return JsonResponse({'message': 'ok', 'code': 200, 'data': data})
    elif request.method == "POST":
        param_list = ['subsystem_name', 'project_id']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({"message": param, "code": 0})
        subsystem_name = param.get("subsystem_name", "")  # 前端传进来的subsystem_name
        subsystem_desc = param.get("subsystem_desc", "")  # 前端传进来的subsystem_desc
        project_id = param.get("project_id", "")  # 前端传进来的subsystem_desc
        if len(subsystem_name) > 18:
            return JsonResponse({"message": "系统名称输入超长", "code": 500})
        if len(subsystem_desc) > 200:
            return JsonResponse({"message": "系统说明输入超长", "code": 500})
        if int(id):
            subsystem_exist = subsystem_obj.filter(subsystem_name=subsystem_name, is_delete=0,
                                                   project_id=project_id).exclude(id=id)
            if subsystem_exist:
                context = {"message": NAME_REPETITION, "code": 500}
                return JsonResponse(context)
            subsystem_info = subsystem_obj.filter(id=id)
            try:
                subsystem_info.update(subsystem_name=subsystem_name, subsystem_desc=subsystem_desc,
                                      update_time=get_time(), username=username)
                object_desc = subsystem_name + '(' + str(id) + ')'
                user_operate(username, "be_edit", "ob_subsystem", object_desc)  # 用户操作记录日志
                context = {'message': EDIT_SUCCESS_200, 'code': 200}
            except Exception as e:
                print(e)
                context = {'message': EDIT_FAIL_500, 'code': 500}
            return JsonResponse(context)
        return JsonResponse({"message": "ID不存在", "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 子系统删除
@login_check
def subsystem_delete(request):
    username = request.session.get("username", "")
    if request.method == "POST":
        # 批量删除
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        ids = param.get("ids")
        # 权限校验
        map_ids = map(str, ids)  # 格式化
        str_ids = ",".join(map_ids)  # 转换成 str 类型
        sql = DELETE_SUBSYSTEM_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        if type(ids) == list:
            del_ids = []
            for id in ids:
                if Sys_env.objects.filter(subsystem_id=id, is_delete=0):
                    return JsonResponse({"message": "删除失败，与测试环境存在关联关系", "code": 500})
                if Inte_interface.objects.filter(subsystem_id=id, is_delete=0):
                    return JsonResponse({"message": "删除失败，与接口存在关联关系", "code": 500})
                if Sys_module.objects.filter(subsystem_id=id, is_delete=0, module_type=1):
                    return JsonResponse({"message": "删除失败，与模块存在关联关系", "code": 500})
                Sys_subsystem.objects.filter(id=id, is_delete=0).update(is_delete=1, username=username,
                                                                        update_time=get_time())
                del_ids.append(id)
            if len(del_ids) == len(ids):
                subsystem_name = Sys_subsystem.objects.get(id=int(str_ids)).subsystem_name
                object_desc = subsystem_name + '(' + str(str_ids) + ')'
                user_operate(username, "be_del", "ob_subsystem", object_desc)  # 用户操作记录日志
                return JsonResponse({"message": DEL_SUCCESSS_200, "code": 200})
        return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 模块列表
@login_check
def module_manager(request, subsystem_id):
    username = request.session.get("username", "")
    if request.method == "POST":
        param_list, result_dict, msg = [], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({"message": param, "code": 0})
        page = param.get("page", 1)  # 分页
        limit = param.get("limit", 10)  # 数量
        # 检验参数
        module_list = MySQLHelper().get_all(MODULE_LIST, (username, subsystem_id))
        total = len(module_list)
        ret = module_list
        sql_params = ['id', 'module_name']
        try:
            data = convert_data(ret, sql_params)
        except Exception as e:
            print(e)
            msg = SERVER_ERROR  # 服务器错误
            data = []
        result_dict['code'] = 0
        result_dict['msg'] = msg if msg else ""
        result_dict['count'] = total
        result_dict['data'] = data
        return JsonResponse(result_dict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 模块新增
@login_check
def module_add(request):
    if request.method == "POST":
        param_list, result_dict, msg = ['module_name', 'subsystem_id', 'env_id'], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({"message": param, "code": 500})
        module_name = param.get("module_name", "")
        module_desc = param.get("module_desc", "")
        subsystem_id = param.get("subsystem_id", "")
        env_id = param.get("env_id", "")
        parent_id = param.get("parent_id", "")
        username = request.session.get("username", "")
        project_permission = MySQLHelper().get_all(SUBSYSTEM_OPERATE, (username, subsystem_id))
        if not project_permission:  # 根据子系统id关联权限表
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        module_exist = Sys_module.objects.filter(module_name=module_name, subsystem_id=subsystem_id,
                                                 is_delete=0)  # 判断重名
        subsystem_id_exist = Sys_subsystem.objects.filter(id=subsystem_id, is_delete=0)  # 判断id存在数据库
        if len(module_name) > 50:
            return JsonResponse({"message": NAME_INPUT_LONG, "code": 500})  # 输入超长提示
        if len(module_desc) > 200:
            return JsonResponse({"message": DESC_INPUT_LONG, "code": 500})  # 输入超长提示
        if module_exist:
            return JsonResponse({"message": NAME_REPETITION, "code": 500})  # 名称重复，抛异常
        if subsystem_id_exist:
            if not parent_id:
                id = Sys_module.objects.create(module_name=module_name, module_desc=module_desc,
                                               subsystem_id=subsystem_id, operater=username,
                                               env_id=env_id, username=username).id
            else:
                parent_module = Sys_module.objects.filter(id=parent_id, is_delete=0)
                if parent_module:
                    # 判断父级模块是否是前置条件、后置条件模块
                    if parent_module[0].module_type == 1:
                        id = Sys_module.objects.create(module_name=module_name, module_desc=module_desc,
                                                       env_id=env_id, subsystem_id=subsystem_id,
                                                       parent_id=parent_id, operater=username,
                                                       username=username).id
                    else:
                        id = Sys_module.objects.create(module_name=module_name, module_desc=module_desc,
                                                       env_id=env_id, subsystem_id=subsystem_id,
                                                       parent_id=parent_id, operater=username,
                                                       module_type=parent_module[0].module_type,
                                                       username=username).id
                else:
                    return JsonResponse({"message": PARENT_MODULE_NOT_FOUND, "code": 500})
            object_desc = module_name + '(' + str(id) + ')'
            user_operate(username, "be_add", "ob_module", object_desc)  # 用户操作记录日志
            return JsonResponse({"message": ADD_SUCCESS_200, "code": 200})
        return JsonResponse({"message": VERSION_NOT_FOUND, "code": 500})  # 系统ID不存在，抛异常
    return JsonResponse({"message": NOT_METHMOD, "code": 500})  # 请求不存在，抛异常


# 模块编辑
@login_check
def module_edit(request, id):
    username = request.session.get("username", "")
    project_permission = MySQLHelper().get_all(GET_PERSON_MODULE, (username, id))
    if not project_permission:  # 根据模块id关联权限表
        return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
    if request.method == "GET":
        info = Sys_module.objects.get(id=id, is_delete=0)
        parent_name = ''
        if info.parent_id:
            parent_name = Sys_module.objects.get(id=info.parent_id, is_delete=0).module_name
        data = {'id': id, 'module_name': info.module_name, 'module_desc': info.module_desc,
                'subsystem_id': info.subsystem_id, 'parent_id': info.parent_id, 'env_id': info.env_id,
                'parent_name': parent_name}
        return JsonResponse({'message': 'ok', 'code': 200, 'data': data})
    elif request.method == "POST":
        param_list = ['module_name', 'subsystem_id']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({"message": param, "code": 500})
        module_name = param.get("module_name", "")
        module_desc = param.get("module_desc", "")
        # parent_id = param.get("parent_id") if param.get("parent_id") else None
        subsystem_id = param.get("subsystem_id", "")
        env_id = param.get("env_id", "")
        info = Sys_module.objects.filter(id=id, is_delete=0)
        # if int(id) == int(parent_id):
        #     return JsonResponse({"message": NOT_CHOOSE_SELF, "code": 500})
        if len(module_name) > 50:
            return JsonResponse({"message": NAME_INPUT_LONG, "code": 500})
        if len(module_desc) > 200:
            return JsonResponse({"message": DESC_INPUT_LONG, "code": 500})
        if int(id):
            exist = Sys_module.objects.filter(module_name=module_name, is_delete=0, subsystem_id=subsystem_id).exclude(
                id=id)  # 编辑的名称已经在数据库
            if exist:
                return JsonResponse({"message": NAME_REPETITION, "code": 500})
            try:
                info.update(module_name=module_name, module_desc=module_desc, update_time=get_time(),
                            env_id=env_id,
                            username=username)  # parent_id=parent_id,
                object_desc = module_name + '(' + str(id) + ')'
                user_operate(username, "be_edit", "ob_module", object_desc)  # 用户操作记录日志
                return JsonResponse({'message': EDIT_SUCCESS_200, 'code': 200})
            except Exception as e:
                print(e)
                return JsonResponse({'message': EDIT_FAIL_500, 'code': 500})
        return JsonResponse({"message": NOT_ID, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 模块删除
@login_check
def module_delete(request):
    username = request.session.get("username", "")
    if request.method == "POST":
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get('ids')
        # 权限校验
        map_ids = map(str, ids)  # 格式化
        str_ids = ",".join(map_ids)  # 转换成 str 类型
        sql = DELETE_MODULE_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        if type(ids) == list:
            del_ids = []
            for id in ids:
                module_exist = Sys_module.objects.filter(parent_id=id, is_delete=0)
                Inte_case_exist = Inte_case.objects.filter(module_id=id, is_delete=0)
                # env_exist = Sys_env.objects.filter(env_id=id, is_delete=0)
                if len(module_exist) != 0 and len(Inte_case_exist) != 0:
                    return JsonResponse({"message": "删除失败，与子模块和用例存在关联关系", "code": 500})
                elif len(Inte_case_exist) != 0:
                    return JsonResponse({"message": "删除失败，与用例存在关联关系", "code": 500})
                elif len(module_exist) != 0:
                    return JsonResponse({"message": "删除失败，与子模块存在关联关系", "code": 500})
                else:
                    Sys_module.objects.filter(id=id, is_delete=0).update(is_delete=1, username=username,
                                                                         update_time=get_time())
                    del_ids.append(id)
            if len(del_ids) == len(ids):
                module_name = Sys_module.objects.get(id=int(str_ids)).module_name
                object_desc = module_name + '(' + str(str_ids) + ')'
                user_operate(username, "be_del", "ob_module", object_desc)  # 用户操作记录日志
                return JsonResponse({"message": DEL_SUCCESSS_200, "code": 200})
        return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 查询加密
@login_check
def encryption_manager(request):
    if request.method == "POST":
        param_list, resultdict, msg = ['project_id'], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({"message": param, "code": 0})
        username = request.session.get('username', '')
        page = param.get("page", 1)  # 分页
        limit = param.get("limit", 10)  # 数量
        project_id = param.get("project_id", '')
        sign_name = param.get("sign_name", '')
        # 检验参数
        sql = ENCRYPTION_LIST % (username, project_id, sign_name)
        list = MySQLHelper().get_all(sql)
        i = (int(page) - 1) * int(limit)
        j = (int(page) - 1) * int(limit) + int(limit)
        ret = list[i:j]
        total = len(list)
        sql_params = ['id', 'variable_name', 'request_method', 'url', 'publickey', 'plaintext', 'extract_field',
                      'encr_type', 'username', 'update_time', 'remark']
        try:
            data = convert_data(ret, sql_params)
        except Exception as e:
            print(e)
            msg = SERVER_ERROR  # 服务器错误
            data = []
        resultdict['code'] = 0
        resultdict['msg'] = msg if msg else ""
        resultdict['count'] = total
        resultdict['data'] = data
        return JsonResponse(resultdict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 新增加密
@login_check
def encryption_add(request):
    username = request.session.get("username", "")
    if request.method == "POST":
        list = ["variable_name", 'request_method', 'publickey', 'plaintext', 'encr_type', 'project_id']
        state, param = params_check(request.body, list)
        if not state:  # 请求参数异常
            return JsonResponse({"message": param, "code": 0})
        variable_name = param.get("variable_name", "")  # 变量名称
        request_method = param.get("request_method", "")  # 请求方法
        url = param.get("url", "")  # URL
        publickey = param.get("publickey", "")  # 公钥
        plaintext = param.get("plaintext", "")  # 明文
        extract_field = param.get("extract_field", "")  # 提取字段
        project_id = param.get("project_id", "")
        encr_type = param.get("encryption_id", 0)  # 加密方法  0 = AI通用  1 = FMS
        remark = param.get("remark", "")  # 备注
        if len(variable_name) > 20:
            return JsonResponse({'message': "加密名称超长！", 'code': 500})
        name_exist = Sys_encryption.objects.filter(variable_name=variable_name, project_id=project_id, is_delete=0)
        project_permission = MySQLHelper().get_all(PROJECT_PERMISSION_CHEKE, (username, project_id))
        if not project_permission:  # 根据项目id关联权限表
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        if name_exist:  # 判断名称重复
            return JsonResponse({"message": NAME_REPETITION, "code": 500})
        try:
            id = Sys_encryption.objects.create(variable_name=variable_name, request_method=request_method,
                                               url=url,
                                               publickey=publickey,
                                               plaintext=plaintext, extract_field=extract_field,
                                               encr_type=encr_type,
                                               username=username, project_id=project_id, remark=remark).id
            object_desc = variable_name + '(' + str(id) + ')'
            user_operate(username, "be_add", "ob_encryption", object_desc)  # 用户操作记录日志
            return JsonResponse({"message": ADD_SUCCESS_200, "code": 200})
        except:
            return JsonResponse({"message": SERVER_ERROR, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})  # 请求不存在，抛异常


# 加密测试
@login_check
def encryption_test(request):
    if request.method == "POST":
        param_list = ['request_method', 'publickey', 'plaintext', 'encr_type']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({"message": param, "code": 0})
        request_method = param.get("request_method", "")  # 请求方法
        url = param.get("url", "")  # URL
        publickey = param.get("publickey", "")  # 公钥
        plaintext = param.get("plaintext", "")  # 明文
        extract_field = param.get("extract_field", "")  # 识别码
        encr_type = param.get("encr_type", "")  # 加密方法  0 = AI通用  1 = FMS
        content = encryption(request_method, url, publickey, plaintext, extract_field, encr_type)
        if content == "加密失败":
            return JsonResponse({"message": "加密失败", "code": 500})
        return JsonResponse({"message": "加密成功", "code": 200, "result":content})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})  # 请求不存在，抛异常


# 编辑加密
@login_check
def encryption_edit(request, id):
    username = request.session.get('username', '')
    project_permission = MySQLHelper().get_all(ENCRYPTION_PROMISSION, (username, id))
    if not project_permission:  # 根据加密id关联权限表
        return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
    if request.method == "GET":
        info = Sys_encryption.objects.get(id=id, is_delete=0)
        data = {'id': id, 'variable_name': info.variable_name, 'request_method': info.request_method, 'url': info.url,
                'publickey': info.publickey,
                'plaintext': info.plaintext, 'extract_field': info.extract_field, 'encr_type': info.encr_type,
                'remark': info.remark}
        return JsonResponse({'message': 'ok', 'code': 200, 'data': data})
    elif request.method == "POST":
        param_list = ["variable_name", 'request_method', 'publickey', 'plaintext', 'encr_type']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({"message": param, "code": 0})
        variable_name = param.get("variable_name", "")  # 变量名称
        request_method = param.get("request_method", "")  # 请求方法
        url = param.get("url", "")  # URL
        publickey = param.get("publickey", "")  # 公钥
        plaintext = param.get("plaintext", "")  # 明文
        extract_field = param.get("extract_field", "")  # 识别码
        encr_type = param.get("encr_type", "")  # 加密方法  0 = AI通用  1 = FMS
        project_id = param.get("project_id", "")
        remark = param.get("remark", "")
        if len(variable_name) > 20:
            return JsonResponse({'message': "加密名称超长！", 'code': 500})
        if int(id):
            exist = Sys_encryption.objects.filter(variable_name=variable_name, is_delete=0,
                                                  project_id=project_id).exclude(
                id=id)  # 编辑名称已经存在数据库
            if exist:
                return JsonResponse({"message": NAME_REPETITION, "code": 500})
            try:
                Sys_encryption.objects.filter(id=id).update(variable_name=variable_name, request_method=request_method,
                                                            url=url, publickey=publickey, update_time=get_time(),
                                                            extract_field=extract_field,
                                                            plaintext=plaintext, encr_type=encr_type,
                                                            username=username, remark=remark)
                object_desc = variable_name + '(' + str(id) + ')'
                user_operate(username, "be_edit", "ob_encryption", object_desc)  # 用户操作记录日志
                return JsonResponse({'message': EDIT_SUCCESS_200, 'code': 200})
            except Exception as e:
                print(e)
                return JsonResponse({'message': EDIT_FAIL_500, 'code': 500})
        return JsonResponse({"message": "ID不存在", "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})  # 请求不存在，抛异常


# 删除加密
@login_check
def encryption_delete(request):
    if request.method == "POST":
        username = request.session.get('username', '')
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get('ids')
        # 权限校验
        map_ids = map(str, ids)  # 格式化
        str_ids = ",".join(map_ids)  # 转换成 str 类型
        sql = DELETE_ENCRYPTION_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        if type(ids) == list:
            del_ids = []
            variable_name = []
            for id in ids:
                name = Sys_encryption.objects.get(id=id).variable_name
                del_ids.append(id)
                variable_name.append(name)
                Sys_encryption.objects.filter(id=id, is_delete=0).update(is_delete=1, username=username,
                                                                         update_time=get_time())
            if len(del_ids) == len(ids):
                object_desc = ",".join(map(str, variable_name)) + '(' + str_ids + ')'
                user_operate(username, "be_del", "ob_encryption", object_desc)  # 用户操作记录日志
                return JsonResponse({"message": DEL_SUCCESSS_200, "code": 200})
        return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 数据驱动管理
@login_check
def dataDriven_manager(request):
    username = request.session.get("username", "")
    if request.method == "POST":
        state, param = params_check(request.body, [])
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        param_name = param.get('param_name', '')
        project_id = param.get("project_id", '')
        page = param.get("page", 1)
        limit = param.get("limit", 10)
        total, data, resultdict = 0, [], {}
        # 检验参数
        i = (int(page) - 1) * int(limit)
        j = (int(page) - 1) * int(limit) + int(limit)

        sql = DATADRIVEN_LIST_LIKE % (username, param_name, project_id)
        param_list = MySQLHelper().get_all(sql)
        total = len(param_list)
        if total > 10:
            sub_param = param_list[i:j]
        else:
            sub_param = param_list
        sql_params = [
            'id', 'param_name', 'remark', 'param_list', 'username', 'update_time', 'creator'
        ]
        data = convert_data(sub_param, sql_params)
        resultdict['code'] = 0
        resultdict['msg'] = ''
        resultdict['count'] = total
        resultdict['data'] = data
        return JsonResponse(resultdict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 数据驱动新增
@login_check
def dataDriven_add(request):
    username = request.session.get("username", "")
    if request.method == 'POST':
        param_list = ['param_name', 'param_list', 'project_id']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        param_name = param.get('param_name', '')
        param_list = param.get('param_list', '')
        project_id = param.get('project_id', '')
        remark = param.get('remark', '')
        dataDriven_list = Sys_data_driven.objects
        project_permission = MySQLHelper().get_all(PROJECT_PERMISSION_CHEKE, (username, project_id))
        if not project_permission:  # 根据项目id关联权限表
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        if len(param_name) > 30:
            return JsonResponse({'message': "参数名称超长！", 'code': 500})
        if dataDriven_list.filter(is_delete=0, param_name=param_name, project_id=project_id):
            return JsonResponse({'message': "该参数名已存在", 'code': 500})
        try:
            id = dataDriven_list.create(
                param_name=param_name,
                param_list=param_list,
                project_id=project_id,
                remark = remark,
                username=username,
                creator=username).id
            object_desc = param_name + '(' + str(id) + ')'
            user_operate(username, "be_add", "ob_data_driven", object_desc)  # 用户操作记录日志
            context = {'message': ADD_SUCCESS_200, 'code': 200}
        except:
            context = {'message': ADD_FAIL_500, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 数据驱动编辑
def dataDriven_edit(request, id):
    username = request.session.get("username", "")
    project_permission = MySQLHelper().get_all(DATADRIVEN_PROMISSION, (username, id))
    if not project_permission:  # 根据模块id关联权限表
        return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
    if request.method == 'GET':
        dataDriven_list = MySQLHelper().get_all(DATADRIVEN_INFO, (id,))
        sql_param = [
            'id', 'param_name', 'param_list', 'project_id', 'remark'
        ]
        data = convert_data(dataDriven_list, sql_param)
        return JsonResponse({'message': 'ok', 'code': 200, 'data': data[0]})
    elif request.method == 'POST':
        param_list = ['param_name', 'param_list', 'project_id']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        param_name = param.get('param_name', '')
        param_list = param.get('param_list', '')
        project_id = param.get('project_id', '')
        remark = param.get('remark', '')
        if len(param_name) > 20:
            return JsonResponse({'message': "参数名称超长！", 'code': 500})
        if int(id):
            exist = Sys_data_driven.objects.filter(param_name=param_name, is_delete=0, project_id=project_id).exclude(
                id=id)  # 编辑名称已经存在数据库
            if exist:
                return JsonResponse({"message": NAME_REPETITION, "code": 500})
            dataDriven_info = Sys_data_driven.objects.filter(id=id, is_delete=0)
            try:
                dataDriven_info.update(
                    param_name=param_name,
                    param_list=param_list,
                    update_time=get_time(),
                    remark = remark,
                    username=username)
                object_desc = param_name + '(' + str(id) + ')'
                user_operate(username, "be_edit", "ob_data_driven", object_desc)  # 用户操作记录日志
                context = {'message': EDIT_SUCCESS_200, 'code': 200}
            except Exception as e:
                print(e)
                context = {'message': EDIT_FAIL_500, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 数据驱动删除
@login_check
def dataDriven_delete(request):
    username = request.session.get("username", "")
    if request.method == "POST":
        # 删除所有
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get("ids")
        # 权限校验
        map_ids = map(str, ids)  # 格式化
        str_ids = ",".join(map_ids)  # 转换成 str 类型
        sql = EDLETE_DATADRIVEN_PERMISSION % (username, str_ids, str_ids)
        project_permission = MySQLHelper().get_all(sql)
        if len(ids) != len(project_permission):
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        del_ids = []
        param_name = []
        if type(ids) == list:
            for id in ids:
                name = Sys_data_driven.objects.get(id=id).param_name
                dataDriven_info = Sys_data_driven.objects.filter(id=id, is_delete=0)
                if len(dataDriven_info) != 0:
                    dataDriven_info.update(is_delete=1, username=username)
                    del_ids.append(id)
                    param_name.append(name)
            if len(ids) == len(del_ids):
                object_desc = ",".join(map(str, param_name)) + '(' + str_ids + ')'
                user_operate(username, "be_del", "ob_data_driven", object_desc)  # 用户操作记录日志
                context = {'message': DEL_SUCCESSS_200, 'code': 200}
            else:
                context = {'message': DEL_FAIL_500, 'code': 500}
            return JsonResponse(context)
        else:
            return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# swagger导入到数据库
@login_check
def swagger_import(request):
    username = request.session.get('username', '')
    if request.method == "POST":
        param_list = ['subsystem_id', 'env_id', 'operate_type']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({"message": param, "code": 500})
        project_id = param.get('project_id', '')
        subsystem_id = param.get('subsystem_id', '')
        env_id = param.get('env_id', '')
        upload_json_data = param.get('upload_json_data', '')
        upload_url = param.get('upload_url', '')
        operate_type = param.get('operate_type', '') # 1=url, 2=json_data
        project_permission = MySQLHelper().get_all(SUBSYSTEM_OPERATE, (username, subsystem_id))
        if not project_permission:  # 根据子系统id关联权限表
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        env_info = Sys_env.objects.filter(id=env_id, is_delete=0)
        if not env_info:
            return JsonResponse({'message': ENV_NOT_FOUND, 'code': 500})
        if env_info[0].subsystem_id != int(subsystem_id):
            return JsonResponse({'message': ENV_NOT_FOUND, 'code': 500})
        if (operate_type == 1 and not upload_url) or (operate_type == '1' and not upload_url):
            return JsonResponse({'message': IMPORT_PARAMS_NOT_URL, 'code': 500})
        if (operate_type == 2 and not upload_json_data) or (operate_type == '2' and not upload_json_data):
            return JsonResponse({'message': IMPORT_PARAMS_NOT_JSON, 'code': 500})
        try:
            data = handle_swagger_param(upload_json_data, upload_url)
            if data == "失败":
                return JsonResponse({'message': "URL错误", 'code': 500})
            if data == "请求超时":
                return JsonResponse({'message': "连接超时，请确认访问策略是否开通", 'code': 500})
        except Exception as e:
            if ("连接尝试失败" in str(e)) or ("504" in str(e)):
                return JsonResponse({'message': "连接超时，请确认访问策略是否开通", 'code': 500})
            return JsonResponse({'message': "导入失败，请确认数据格式是否正确", 'code': 500})
        repeat, context = [], {}
        err_list = []
        try:
            for i in data:
                is_exist = Inte_interface.objects.filter(is_delete=0, req_method=i[2], req_path=i[1],
                                                         subsystem_id=subsystem_id,project_id=project_id)
                if is_exist:  # 判断是否重复导入，如果重复当前数据不导入继续下一条导入操作
                    err_dict = {'err_msg': '重复导入', 'interface_name': i[0], 'method': i[2], 'path': i[1]}
                    err_list.append(err_dict)
                    continue
                try:
                    Inte_interface.objects.create(create_time=get_time(), update_time=get_time(), is_delete=0,
                                                  interface_name=i[0].strip(),
                                                  req_path=i[1],
                                                  req_method=i[2], req_headers=i[3], req_param=i[4], req_body=i[5],
                                                  username=username, project_id=project_id, creator=username,
                                                  subsystem_id=subsystem_id, env_id=env_id, state=1)
                except Exception as e:
                    print(e)
                    err_dict = {'err_msg': str(e), 'interface_name': i[0], 'method': i[2], 'path': i[1]}
                    err_list.append(err_dict)
            count = len(data)
            err_count = len(err_list)
            success_count = count - err_count
            subsystem_name = Sys_subsystem.objects.get(id=int(subsystem_id)).subsystem_name
            object_desc = subsystem_name + '(' + str(subsystem_id) + ')'
            user_operate(username, "be_import_interface", "ob_subsystem", object_desc)  # 用户操作记录日志
            return JsonResponse({"message": "导入信息", "code": 200, "count": count, "success_count": success_count,
                                 "err_count": err_count, "err_list": err_list})
        except Exception as e:
            print(e)
            return JsonResponse({"message": "导入失败", "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 复制子系统
@login_check
def subsystem_copy(request):
    username = request.session.get('username', '')
    if request.method == "POST":
        state, param = params_check(request.body, ['subsystem_id'])
        if not state:
            return JsonResponse({"message": param, "code": 500})
        subsystem_id = param.get('subsystem_id', '')
        project_permission = MySQLHelper().get_all(SUBSYSTEM_OPERATE, (username, subsystem_id))
        if not project_permission:  # 根据子系统id关联权限表
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        subsystem_id_exist = Sys_subsystem.objects.filter(id=subsystem_id)  # 校验当前id是否存在数据库
        module_exist = Sys_module.objects.filter(subsystem_id=subsystem_id)  # 校验当前系统id是否与模块有关联
        interface_exist = Inte_interface.objects.filter(subsystem_id=subsystem_id)  # 校验当前系统id是否与接口有关联
        if subsystem_id_exist and module_exist and interface_exist:
            result = copy_subsystem(subsystem_id, username)
            if result == "复制成功":
                subsystem_name = Sys_subsystem.objects.get(id=int(subsystem_id)).subsystem_name
                object_desc = subsystem_name + '(' + str(subsystem_id) + ')'
                user_operate(username, "be_copy", "ob_subsystem", object_desc)  # 用户操作记录日志
                return JsonResponse({"message": "复制成功！", "code": 200})
            elif result == "名称重复":
                return JsonResponse({"message": "当前子系统已复制！", "code": 500})
            elif result == "名称超长":
                return JsonResponse({"message": "名称超长！", "code": 500})
            else:
                return JsonResponse({"message": "复制失败:%s" % result, "code": 500})
        elif not subsystem_id_exist:
            return JsonResponse({"message": "复制失败,系统不存在！", "code": 500})
        elif not module_exist:
            return JsonResponse({"message": "系统中无模块复制失败", "code": 500})
        elif not interface_exist:
            return JsonResponse({"message": "系统中无接口复制失败", "code": 500})
        return JsonResponse({"message": "复制失败！", "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 复制任务
@login_check
def task_copy(request):
    username = request.session.get('username', '')
    if request.method == "POST":
        state, param = params_check(request.body, ['task_id'])
        if not state:
            return JsonResponse({"message": param, "code": 500})
        task_id = param.get('task_id', '')
        project_permission = MySQLHelper().get_all(TASK_PERMISSION, (username, task_id))
        if not project_permission:  # 根据任务id关联权限表
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        if Inte_task.objects.filter(id=task_id, is_delete=0, state=1):
            return JsonResponse({"message": "任务运行中，禁止复制！", "code": 500})
        task_exist = Inte_task.objects.filter(id=task_id)
        task_case_exist = Inte_task_case.objects.filter(task_id=task_id)
        if task_exist and task_case_exist:
            result, new_task_id= copy_task(task_id, username)
            if result == "名称重复":
                return JsonResponse({"message": "当前任务已复制！", "code": 500})
            if result == "复制成功":
                log_task_name = Inte_task.objects.get(id=int(task_id)).task_name
                copy_name = Inte_task.objects.get(id=int(new_task_id)).task_name
                cron = Inte_task.objects.get(id=task_id).cron
                password = Sys_user_info.objects.get(username=username,is_delete=0).password
                email = Sys_user_info.objects.get(username=username, is_delete=0).email
                job_id, result = add_scheduler(copy_name, username, password, cron, new_task_id, email)
                if result["msg"] == "Cron非法":
                    return JsonResponse({"message": "计划时间格式错误", "code": 500})
                Inte_task.objects.filter(id=new_task_id, is_delete=0).update(job_id=job_id)
                if job_id == None:
                    Inte_task.objects.filter(id=new_task_id, is_delete=0).update(is_delete=1)
                    return JsonResponse({"message": "调度平台添加异常", "code": 500})
                object_desc = log_task_name + '(' + str(task_id) + ')'
                user_operate(username, "be_copy", "ob_task", object_desc)  # 用户操作记录日志
                return JsonResponse({"message": "复制成功！", "code": 200})
            if result == "名称超长":
                return JsonResponse({"message": "名称超长！", "code": 500})
            return JsonResponse({"message": "复制失败:%s" % result, "code": 500})
        if not task_exist:
            return JsonResponse({"message": "复制失败，当前ID不存在！", "code": 500})
        if not task_case_exist:
            return JsonResponse({"message": "复制失败，当前任务没有用例", "code": 500})
        return JsonResponse({"message": "复制失败！", "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


@login_check
def report_export(request):
    username = request.session.get("username", "")
    if request.method == "POST":
        state, param = params_check(request.body, ["task_id"])
        if not state:
            return JsonResponse({"message": param, "code": 500})
        task_id = param.get("task_id", "")
        project_permission = MySQLHelper().get_all(TASK_PERMISSION, (username, task_id))
        if not project_permission:  # 根据任务id关联权限表
            return JsonResponse({"message": NOT_PERMISSION, "code": 500})

    return JsonResponse({"message": NOT_METHMOD, "code": 500})



# 移动用例
@login_check
def move_case(request):
    username = request.session.get('username', '')
    if request.method == "POST":
        state, param = params_check(request.body, ['module_id', 'case_ids', 'new_moduleId'])
        if not state:
            return JsonResponse({"message": param, "code": 500})
        module_id = param.get("module_id", "")
        case_ids = param.get("case_ids", "")
        new_moduleId = param.get("new_moduleId", "")
        new_moduleId_exist = Sys_module.objects.filter(id=new_moduleId)  # 判断新模块id是否存在
        if not new_moduleId_exist:
            return JsonResponse({'message': "目标模块不存在！", 'code': 500})
        new_subsystemId = Sys_module.objects.get(id=new_moduleId, is_delete=0).subsystem_id  # 通过新模块id获取新子系统id
        new_projectId = Sys_subsystem.objects.get(id=new_subsystemId, is_delete=0).project_id  # 通过传进来的子系统id，获取项目id
        new_envId_exist = Sys_env.objects.filter(subsystem_id=new_subsystemId, is_delete=0)  # 判断新项目子系统是否存在环境
        # 项目权限校验
        project_permission = MySQLHelper().get_all(PROJECT_PERMISSION_CHEKE, (username, new_projectId))
        if not project_permission:
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        if not new_envId_exist:
            return JsonResponse({'message': "当前子系统没有环境！", 'code': 500})
        if type(case_ids) == list:
            try:
                # 获取新的环境 id
                sql = """SELECT id from sys_env where subsystem_id = %s""" % (new_subsystemId)
                env_list = MySQLHelper().get_all(sql)
                new_envId = env_list[0][0]

                # 校验用例是否被任务勾选
                str_ids = ",".join(map(str, case_ids))  # 转换成 str 类型
                task_sql = SELECT_CASE_TO_TASK % (str_ids, str_ids)
                case_id_exist = convert_data(MySQLHelper().get_all(task_sql), ['case_id'])
                if case_id_exist:  # 用例被任务勾选
                    id = case_id_exist[0]["case_id"]
                    case_name = Inte_case.objects.get(id=int(id)).case_name
                    return JsonResponse({"message": "用例:%s被任务勾选，禁止移动！" % case_name, "code": 500})
                # 校验用例与模块是否关联
                for id in case_ids:
                    case_info = Inte_case.objects.get(id=id)
                    module_id_exist = case_info.module_id
                    if str(module_id_exist) != str(module_id):
                        module_name = Sys_module.objects.get(id=module_id_exist).module_name
                        return JsonResponse(
                            {"message": "用例:%s 与模块:%s 没有关联关系" % (case_info.case_name, module_name), "code": 500})
                for id in case_ids:
                    extract_list = Inte_case.objects.get(id=id, is_delete=0).extract_list  # 通过用例id关联，获取依赖数据列表
                    interface_id = Inte_case.objects.get(id=id, is_delete=0).interface_id  # 通过用例id关联，获取接口id
                    # 用例依赖数据迁移
                    if extract_list:
                        extract_list = extract_list.split(',')
                        for extract_id in extract_list:
                            Inte_extract.objects.filter(id=extract_id, is_delete=0).update(project_id=new_projectId)
                    # 当前子系统存在环境
                    if new_envId:
                        Inte_interface.objects.filter(id=interface_id).update(env_id=int(new_envId))
                    # 把用例迁移到新模块
                    Inte_case.objects.filter(id=id, is_delete=0).update(module_id=new_moduleId, username=username)
                    # 把用例关联的接口迁移到新子系统
                    Inte_interface.objects.filter(id=interface_id, is_delete=0).update(subsystem_id=new_subsystemId,
                                                                                       username=username)
                    # 移除旧模块 case_list 字段用例id
                    case_list = Sys_module.objects.filter(id=module_id)[0].case_list.split(',')
                    case_list.remove(str(id))
                    Sys_module.objects.filter(id=module_id).update(case_list=','.join(case_list))
                # 更新新模块 case_list 字段值
                case_list = Sys_module.objects.get(id=new_moduleId, is_delete=0).case_list
                str_list = [str(x) for x in case_list.split(',') if str(x)] + [str(x) for x in case_ids if str(x)]
                case_list = ','.join(str_list)
                sql = """UPDATE sys_module set case_list='%s' WHERE id = %s""" % (case_list, new_moduleId)
                MySQLHelper().update(sql)
                # 操作记录日志
                module_name = Sys_module.objects.get(id=int(module_id)).module_name
                new_module_name = Sys_module.objects.get(id=int(new_moduleId)).module_name
                object_desc = "旧模块:" + module_name + ",用例集:(" + str_ids + "),新模块:" + new_module_name
                user_operate(username, "be_move", "ob_case", object_desc)
                return JsonResponse({"message": "迁移成功！", "code": 200})
            except Exception as e:
                print(e)
                return JsonResponse({"message": "迁移失败", "code": 500})
        return JsonResponse({"message": "case_ids类型不是list", "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 用例与接口导出
@login_check
def export_excel(request):
    if request.method == "POST":
        username = request.session.get("username", "")
        state, param = params_check(request.body, ["subsystem_id", "type"])
        if not state:
            return JsonResponse({"message": param, "code": 500})
        subsystem_id = param.get("subsystem_id", "")
        type = param.get("type", "")
        # 子系统权限校验
        subsystem_permission = MySQLHelper().get_all(SUBSYSTEM_OPERATE, (username, subsystem_id))
        if not subsystem_permission:
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        subsystem_name = Sys_subsystem.objects.get(id=subsystem_id).subsystem_name
        object_desc = subsystem_name + "(" + str(subsystem_id) + ")"
        if type == "case":
            file_name = subsystem_name + "_用例导出.xlsx"
            export_data, headers = exprot_case(subsystem_id)
            if export_data:
                # 操作记录日志
                user_operate(username, "be_export_case", "ob_subsystem", object_desc)
                return JsonResponse({'message': "导出成功", 'code': 200, 'file_name': file_name,
                                     'format': 'xlsx', 'headers': headers, 'data': export_data})
            return JsonResponse({"message": "没有可以导出的用例！", "code": 500})
        if type == "interface":
            file_name = subsystem_name + "_接口导出.xlsx"
            export_data, headers = export_interface(subsystem_id)
            if export_data:
                # 操作记录日志
                user_operate(username, "be_export_interface", "ob_subsystem", object_desc)
                return JsonResponse({'message': "导出成功", 'code': 200, 'file_name': file_name,
                                     'format': 'xlsx', 'headers': headers, 'data': export_data})
            return JsonResponse({"message": "没有可以导出的接口！", "code": 500})
        return JsonResponse({"message": "type error", "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 用户日志
@login_check
def user_operate_record(request):
    if request.method == "POST":
        user_name = request.session.get("username", "")
        role = Sys_user_info.objects.filter(username=user_name, is_delete=0)[0].role
        if role != 1:
            return JsonResponse({"message": NOT_PERMISSION, "code": 500})
        state, param = params_check(request.body, [])
        if not state:
            return JsonResponse({"message": param, "code": 500})
        begin_time = param.get("beginTime", "")  # 开始时间
        end_time = param.get("endTime", "")  # 结束时间
        username = param.get("username", "")  # 操作人
        behavior = param.get("behavior", "")  # 行为
        page = param.get("page", 1)
        limit = param.get("limit", 10)
        if (begin_time and not end_time) or (end_time and not begin_time):
            return JsonResponse({"message": "日期不完整！", "code": 500})
        param_sql = ["operate_time", "username", "behavior", "object_name", "object_desc"]
        begin_time = begin_time + ":00"
        end_time = end_time + ":59"
        sql = SELECT_OPERATE % (begin_time, end_time, begin_time, end_time, behavior, behavior, username, page, limit)
        param_list = MySQLHelper().get_all(sql)
        count_sql = COUNT_OPERATE % (begin_time, end_time, begin_time, end_time, behavior, behavior, username)
        total = MySQLHelper().get_all(count_sql)
        data = convert_data(param_list, param_sql)
        return JsonResponse({"message": "ok", "code": 0, "count": total[0][0], "data": data})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


# 操作记录行为列表
@admin_check
def operate_list(request):
    if request.method == "GET":
        param_list = MySQLHelper().get_all(SELECT_OPERATE_TYPE)
        sql_params = ['id', 'dict_key', 'dict_value']
        rule_data = convert_data(param_list, sql_params)
        return JsonResponse({'code': 200, 'data': rule_data})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


'''对接Dveops流水线平台'''


@login_check
def bat_run_task(request):
    username = request.session.get("username", "")
    if request.method == "POST":
        state, param = params_check(request.body, ["task_name", "project_name", "host"])
        if not state:
            return JsonResponse({"message": param, "code": 500})
        task_name = param.get("task_name", "").strip()
        project_name = param.get("project_name", "").strip()
        host = param.get("host", "").strip()
        project_info = Sys_project.objects.filter(project_name=project_name, is_delete=0)
        if not project_info:
            return JsonResponse({"message": PROJECT_NOT_FOUND, "code": 500})
        try:
            task_info = Inte_task.objects.get(task_name=task_name, is_delete=0, project_id=project_info[0].id)
        except:
            return JsonResponse({"message": TASK_NOT_FOUND, "code": 500})
        task_id = task_info.id  # 获取任务id
        project_permission = MySQLHelper().get_all(TASK_PERMISSION, (username, task_id))  # 校验权限
        if not project_permission:
            return JsonResponse({'message': NOT_PERMISSION, 'code': 500})
        task_list = task_info.case_list  # 获取用例列表
        if not task_list:
            return JsonResponse({"message": TASK_IS_EMPTY, "code": 500})
        task_list = (','.join([x for x in list(eval(task_list).values()) if x])).strip(',')
        subsystem_dict = list(eval(task_info.case_dict).keys())
        interface_count = len(Inte_interface.objects.filter(subsystem_id__in=subsystem_dict, is_delete=0, state=1))
        # 任务用例
        sql = BAT_EXECTUE_TASK % (interface_count, username, task_id, task_list, task_list)
        sql_result = MySQLHelper().get_all(sql)
        sql_params = [
            'id', 'case_name', 'module_id', 'module_name', 'req_method', 'req_path', 'req_headers',
            'req_param', 'req_body', 'req_file', 'extract_list', 'except_list', 'interface_count', 'subsystem_id',
            'run_time', 'wait_time', 'module_type', 'interface_id', 'project_id', 'type'
        ]
        task_data = convert_one_to_many_data(sql_result, sql_params, False)
        [x.update({"host": host, "port": ""}) for x in task_data]
        task_detail = convert_runtime(task_data)  # 任务详情
        # 在数据库插入数据
        report_id = Inte_report.objects.create(is_delete=0, task_id=task_id, username=username, report_type=1,
                                               job_status=1).id

        # 新建一个线程
        class PrintThread(threading.Thread):
            def run(self):
                Test.test_suite(task_detail, "task", str(task_id), username, task_name, task_info.project_id, report_id,
                                1)

        try:
            PrintThread().start()
            user_operate(username, "be_now_run", "ob_task", str(task_id))  # 用户操作记录日志
            return JsonResponse({"isStartTest": True, "code": 200, "report_id": report_id})
        except:
            return JsonResponse({"isStartTest": False, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


'''查询执行任务接口情况'''


@login_check
def get_run_task(request):
    if request.method == "POST":
        state, param = params_check(request.body, ["report_id"])
        if not state:
            return JsonResponse({"message": param, "code": 500})
        id = param.get("report_id", "")
        username = request.session.get('username', '')
        sql = SELECT_REPORT % (id, username)
        sql_param = ['report_path', 'job_status', 'job_count']
        data_list = convert_data(MySQLHelper().get_all(sql), sql_param)
        if not data_list:
            return JsonResponse({"message": "报告不存在！", "code": 500})
        dict_data = {}
        for i in data_list:
            dict_data = i
        if dict_data["report_path"] == "" or dict_data["job_count"] == "":
            data = {"testStatus": 1, "isPass": False, "reportLink": "", "sampleCount": 0, "errorCount": 0,
                    "errorPct": "0%"}
            return JsonResponse({"message": "ok", "code": 200, "data": data})
        job_status = dict_data["job_status"]  # 执行状态
        host = request.get_host()  # 获取当前服务的 ip 地址
        report_path = "http://" + host + dict_data["report_path"]  # 报告链接
        job_count = json.loads(dict_data["job_count"])  # 用例数
        sampleCount = job_count["sampleCount"]  # 任务用例总数
        errorCount = job_count["errorCount"]  # 任务用例失败数
        errorPct = '{:.2f}%'.format(errorCount / sampleCount * 100)  # 错误率
        if int(errorCount) > 0:
            isPass = False
        else:
            isPass = True
        data = {"testStatus": job_status, "isPass": isPass, "reportLink": report_path, "sampleCount": sampleCount,
                "errorCount": errorCount, "errorPct": errorPct}
        return JsonResponse({"message": "ok", "code": 200, "data": data})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})

def sz_test_notify(request):
    if request.method == "POST":
        state, param = params_check(request.body, ["id"])
        if not state:
            return JsonResponse({"message": param, "code": 500})
        id = param.get("id", "")
        signature = request.GET.get("signature", "")
        param = json.loads(json.dumps(request.GET))
        del param["signature"]
        urls = []
        for key, value in param.items():
            u = key + "=" + value + "&"
            urls.append(u)
        urls = "".join(urls)[:-1]
        body = json.dumps(json.loads(request.body)).replace(" ", "")
        url = "/api/notify?" + urls
        data = "POST" + "\n" + url + "\n" + body + "\n"
        clientSecret = ''.join(MySQLHelper().get_one("""select dict_value from `sys_dict` where dict_type=7"""))
        secret = clientSecret + ":" + data
        sha256 = hashlib.sha256(secret.encode('utf-8')).hexdigest()
        if sha256 == signature:
            Sys_notify.objects.create(create_time=get_time(), update_time=get_time(), is_delete=0,
                                      status=1, desc="sz-test", order_id=id, username="admin")
            data = {"body": body, "message": "订单执行完毕", "signature": sha256}
            user_operate("notifytest", "200", id, data)
            return JsonResponse({"message": "订单执行完毕", "code": 200, "signature": sha256})
        else:
            user_operate("notifytest", "400", id, "测试环境签名验证失败")
            return HttpResponse(status=400)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})

def notify(request):
    if request.method == "POST":
        state, param = params_check(request.body, ["id"])
        if not state:
            return JsonResponse({"message": param, "code": 500})
        id = param.get("id", "")
        signature = request.GET.get("signature", "")
        param = json.loads(json.dumps(request.GET))
        del param["signature"]
        urls = []
        for key, value in param.items():
            u = key + "=" + value + "&"
            urls.append(u)
        urls = "".join(urls)[:-1]
        body = json.dumps(json.loads(request.body)).replace(" ", "")
        url = "/api/notify?" + urls
        data = "POST" + "\n" + url + "\n" + body + "\n"
        clientSecret = ''.join(MySQLHelper().get_one("""select dict_value from `sys_dict` where dict_type=6"""))
        secret = clientSecret + ":" + data
        sha256 = hashlib.sha256(secret.encode('utf-8')).hexdigest()
        if sha256 == signature:
            Sys_notify.objects.create(create_time=get_time(), update_time=get_time(), is_delete=0,
                                      status=1, desc="dev", order_id=id, username="admin")
            data = {"body":body, "message":"订单执行完毕", "signature": sha256}
            user_operate("notify", "200", id, data)
            return JsonResponse({"message": "订单执行完毕", "code": 200, "signature": sha256})
        else:
            user_operate("notify", "400", id, "dev环境签名验证失败")
            return HttpResponse(status=400)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})

def notifyfail(request):
    user_operate("notify", "400", "wms-mock接口", "dev环境错误信息：400")
    return HttpResponse(status=400)

def sz_test_fail(request):
    user_operate("notifytest", "400", "wms-mock接口", "sz-test环境错误信息：400")
    return HttpResponse(status=400)

def notify500(request):
    user_operate("notify", "500", "wms-mock接口", "dev环境错误信息：500")
    return HttpResponse(status=500)

def sz_test_500(request):
    user_operate("notifytest", "500", "wms-mock接口", "sz-test环境错误信息：500")
    return HttpResponse(status=500)

def notify_log(request):
    if request.method == "GET":
        behavior = request.GET.get("status", "")
        object_name = request.GET.get("id", "")
        param_sql = ["operate_time", "username", "status", "id", "log"]
        sql = NOTIFY_SQL % (behavior, behavior, object_name, object_name)
        param_list = MySQLHelper().get_all(sql)
        data = convert_data(param_list, param_sql)
        total = len(param_list)
        return JsonResponse({"message": "ok", "code": 200, "total":total, "data": data})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})

def sz_test_log(request):
    if request.method == "GET":
        behavior = request.GET.get("status", "")
        object_name = request.GET.get("id", "")
        param_sql = ["operate_time", "username", "status", "id", "log"]
        sql = NOTIFY_SQL_TEST % (behavior, behavior, object_name, object_name)
        param_list = MySQLHelper().get_all(sql)
        data = convert_data(param_list, param_sql)
        total = len(param_list)
        return JsonResponse({"message": "ok", "code": 200, "total": total, "data": data})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})