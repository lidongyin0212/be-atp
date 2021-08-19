from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from UITestManage.models import *
from InterfaceTestManage.models import *

from public.publicfun import params_check, MySQLHelper, handle_ui_case_data, convert_ui_data, get_time, login_check
from .utils.UITestRun import Test
from .utils.sql_manager import *
from constant import *
from .utils.command import *
from multiprocessing import Process
from public.thread_manage import *


# Create your views here.


@login_check
def case_manager(request):
    # 用例列表
    username = request.session.get("username", "")
    if request.method == "GET":
        return render(request, 'ui_case/case-list.html')
    elif request.method == "POST":
        param_list, resultdict, msg = [], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        type = param.get('type', '')
        if type == 'tree':
            subsystem_id = param.get('subsystem_id', '')
            subsystem_info = Sys_subsystem.objects.filter(id=subsystem_id, is_delete=0)
            if not subsystem_info:
                return JsonResponse({"message": SUBSYSTEM_NOT_FOUND, "code": 500}, safe=False)
            sql = CASE_TREE % (username, subsystem_id)
            result = MySQLHelper().get_all(sql)
            result = handle_ui_case_data(result)
            return JsonResponse({'data': [{"title": subsystem_info[0].subsystem_name,
                                           "id": subsystem_info[0].id,
                                           "children": result,
                                           'level': 0, 'spread': True}]})
        elif type == 'table':
            page = param.get("page", 1)
            limit = param.get("limit", 10)
            case_name = param.get("case_name", "")
            subsystem_id = param.get("subsystem_id", 0)
            i = (int(page) - 1) * int(limit)
            j = (int(page) - 1) * int(limit) + int(limit)
            sql = CASE_LIST_LIKE % (username, case_name, subsystem_id)
            case_list = MySQLHelper().get_all(sql)
            sub_case = case_list[i:j]
            total = len(case_list)
            sql_params = [
                'id', 'case_name', 'case_desc', 'project_id', 'project_name', 'step_list',
                'username', 'update_time'
            ]
            try:
                data = convert_ui_data(sub_case, sql_params)
            except Exception as e:
                print(e)
                msg = SERVER_ERROR
                data = []
            resultdict['code'] = 0
            resultdict['msg'] = msg if msg else ""
            resultdict['count'] = total
            resultdict['data'] = data
            return JsonResponse(resultdict, safe=False)
        return JsonResponse({"message": NOT_TYPE, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


@login_check
def case_add(request):
    # 用例添加
    if request.method == 'POST':
        # 用例接口添加
        param_list = ['case_name', 'subsystem_id']
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        username = request.session.get("username", '').strip()
        case_name = params.get('case_name', '').strip()
        subsystem_id = params.get('subsystem_id', '').strip()
        case_desc = params.get('case_desc', '').strip()
        step_list = params.get('step_list', '')
        ui_case = UI_Case.objects
        subsystem_permission = MySQLHelper().get_all(GET_PERSON_SUBSYSTEM, (username, subsystem_id))
        if len(subsystem_permission):
            case_is_exists = ui_case.filter(case_name=case_name, is_delete=0, subsystem_id=subsystem_id)
            if case_is_exists:
                return JsonResponse({'message': '该用例名已存在', 'code': 500})
            if len(case_name) > 0 and len(subsystem_id):
                case_id = ui_case.create(
                    case_name=case_name,
                    subsystem_id=subsystem_id,
                    case_desc=case_desc,
                    step_list=step_list,
                    username=username).id
                context = {'message': ADD_SUCCESS_200, 'code': 200, 'id': case_id}
            else:
                context = {'message': ADD_FAIL_500, 'code': 500}
        else:
            context = {'message': NOT_PERMISSION, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


@login_check
def case_edit(request, id):
    # 用例编辑
    if request.method == 'GET':
        username = request.session.get('username', '')
        case_param = ["id", "case_name", "case_desc", "project_id", "step_list"]
        case_info = convert_ui_data(
            MySQLHelper().get_all(SELECT_CASE_INFO, (username, id)), case_param)
        case_info = case_info[0] if case_info else []
        return JsonResponse({'message': 'ok', 'code': 200, 'data': [case_info]})
    elif request.method == 'POST':
        param_list = ['case_name', 'project_id']
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        case_name = params.get('case_name', '')
        subsystem_id = params.get('subsystem_id', '').strip()
        case_desc = params.get('case_desc', '')
        username = request.session.get("username", '')
        step_list = params.get('step_list', '')
        project_permission = MySQLHelper().get_all(GET_PERSON_SUBSYSTEM, (username, subsystem_id))
        if len(project_permission):
            ui_case = UI_Case.objects
            case_is_exists = ui_case.filter(case_name=case_name, is_delete=0, subsystem_id=subsystem_id).exclude(id=id)
            if case_is_exists:
                return JsonResponse({'message': '该用例名已存在', 'code': 500})
            ui_case_info = ui_case.filter(id=id)
            try:
                ui_case_info.update(
                    case_name=case_name,
                    subsystem_id=subsystem_id,
                    case_desc=case_desc,
                    step_list=step_list,
                    username=username,
                    update_time=get_time())
                context = {'message': EDIT_SUCCESS_200, 'code': 200}
            except Exception as e:
                print(e)
                context = {'message': EDIT_FAIL_500, 'code': 500}
        else:
            context = {'message': NOT_PERMISSION, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


@login_check
def case_delete(request):
    # 用例删除
    username = request.session.get("username", "")
    if request.method == "POST":
        # 删除所有
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get("ids")
        del_ids = []
        if type(ids) == list:
            for id in ids:
                UI_Case.objects.filter(id=id, is_delete=0).update(is_delete=1)
                del_ids.append(id)
            if len(del_ids) == len(ids):
                context = {'message': DEL_SUCCESSS_200, 'code': 200}
            else:
                context = {'message': USING_MSG % '任务', 'code': 500}
            return JsonResponse(context)
        else:
            return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


@login_check
def role_node(request):
    username = request.session.get("username", "")
    if request.method == "GET":
        return render(request, 'ui_case/node-list.html')
    elif request.method == "POST":
        param_list, resultdict, msg = [], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        page = param.get("page", "")
        limit = param.get("limit", "")
        username = param.get("case_name", "")
        project_id = param.get("project_id", 0)
        i = (int(page) - 1) * int(limit)
        j = (int(page) - 1) * int(limit) + int(limit)
        sql = CASE_LIST_LIKE % (username, case_name, project_id, project_id)
        case_list = MySQLHelper().get_all(sql)
        sub_case = case_list[i:j]
        total = len(case_list)
        sql_params = [
            'id', 'case_name', 'case_desc', 'project_id', 'project_name', 'step_list',
            'username', 'update_time'
        ]
        try:
            data = convert_ui_data(sub_case, sql_params)
        except Exception as e:
            print(e)
            msg = SERVER_ERROR
            data = []
        for i in data:
            if i['step_list'] == '':
                i['count'] = 0
            else:
                i['count'] = len(eval(i['step_list']))
        resultdict['code'] = 0
        resultdict['msg'] = msg if msg else ""
        resultdict['count'] = total
        resultdict['data'] = data
        return JsonResponse(resultdict, safe=False)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


@login_check
def node_add(request):
    # 节点添加
    if request.method == 'POST':
        param_list = ['node_name', 'node_ip', 'node_port', 'browser']
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        username = request.session.get("username", '')
        node_name = params.get('node_name', '').strip()
        node_ip = params.get('node_ip', '').strip()
        node_port = params.get('node_port', '').strip()
        browser = params.get('browser', '')
        ui_node_list = UI_Node.objects
        node_name_is_exists = ui_node_list.filter(node_name=node_name, is_delete=0)
        if node_name_is_exists:
            return JsonResponse({'message': '该用例名已存在', 'code': 500})
        node_port_is_exists = ui_node_list.filter(node_port=node_port, is_delete=0)
        if node_port_is_exists:
            return JsonResponse({'message': '该端口已存在，请换其他端口', 'code': 500})
        if len(node_name) > 0 and len(node_ip) > 0 and len(node_port) > 0 and len(browser) > 0:
            ui_node_list.create(
                node_name=node_name,
                node_ip=node_ip,
                node_port=node_port,
                browser=browser,
                username=username,
                create_time=get_time())
            context = {'message': ADD_SUCCESS_200, 'code': 200}
        else:
            context = {'message': ADD_FAIL_500, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


@login_check
def node_edit(request, id):
    # 节点编辑
    if request.method == 'GET':
        username = request.session.get('username', '')
        node_param = ['id', 'node_name', 'node_ip', 'node_port', 'browser', 'state']
        node_info = convert_ui_data(
            MySQLHelper().get_all(SELECT_NODE_INFO, (id,)), node_param)
        node_info = node_info[0] if node_info else []
        return JsonResponse({'message': 'ok', 'code': 200, 'data': node_info})
    elif request.method == 'POST':
        param_list = []
        state, params = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': params, 'code': 500})
        node_name = params.get('node_name', '').strip()
        node_ip = params.get('node_ip', '').strip()
        node_port = params.get('node_port', '').strip()
        browser = params.get('browser', '').strip()
        username = request.session.get("username", '')
        ui_node_list = UI_Node.objects
        node_name_is_exists = ui_node_list.filter(node_name=node_name, is_delete=0).exclude(id=id)
        if node_name_is_exists:
            return JsonResponse({'message': '该用例名已存在', 'code': 500})
        node_port_is_exists = ui_node_list.filter(node_port=node_port, is_delete=0).exclude(id=id)
        if node_port_is_exists:
            return JsonResponse({'message': '该端口已经存在，请换其他端口', 'code': 500})
        ui_node_info = ui_node_list.filter(id=id)
        try:
            ui_node_info.update(
                node_name=node_name,
                node_ip=node_ip,
                node_port=node_port,
                browser=browser,
                username=username,
                update_time=get_time())
            context = {'message': EDIT_SUCCESS_200, 'code': 200}
        except Exception as e:
            print(e)
            context = {'message': EDIT_FAIL_500, 'code': 500}
        return JsonResponse(context)
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


@login_check
def node_delete(request):
    # 用例删除
    username = request.session.get("username", "")
    if request.method == "POST":
        # 删除所有
        param_list = ['ids']
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        ids = param.get("ids")
        del_ids = []
        if type(ids) == list:
            for id in ids:
                UI_Node.objects.filter(id=id, is_delete=0).update(is_delete=1)
                del_ids.append(id)
            if len(del_ids) == len(ids):
                context = {'message': DEL_SUCCESSS_200, 'code': 200}
            else:
                context = {'message': DEL_FAIL_500, 'code': 500}
            return JsonResponse(context)
        else:
            return JsonResponse({"message": NOT_LIST, "code": 500})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})


@login_check
def execute_cases(request, id):
    if request.method == "POST":
        case_info = UI_Case.objects.filter(id=id)[0]
        if not case_info.step_list:
            return JsonResponse({"message": "用例为空", "code": 404})

        # 执行测试用例
        case_name = case_info.case_name
        return runCase(case_info.step_list, id, case_name, username, case_info.project_id)


def runCase(case_step_info, id, case_name, username, project_id):
    # 用例运行
    try:
        response = Test.test_suite(case_step_info, "case", id, case_name, project_id)
        case_desc = None
        for res_data in response:
            if '失败' == res_data[4]:
                break
        else:
            case_desc = 1
        if case_desc:
            content = {"message": EXECUTE_CASE_SUCCESS, "code": 200, 'id': id, 'case_name': case_name}
        else:
            content = {"message": EXECUTE_CASE_FAIL, "code": 500, 'id': id, 'case_name': case_name}
        return JsonResponse(content)
    except Exception as e:
        content = {
            "message": EXECUTE_CASE_EXCEPT % str(e),
            "code": "500",
            'id': id,
            'case_name': case_name
        }
        return JsonResponse(content)


@login_check
def case_report(request, id):
    if request.method == "GET":
        return render(request, 'ui_case/case_report.html', {"case_id": id})
    elif request.method == "POST":
        page = request.POST.get('page')
        rows = request.POST.get('limit')
        i = (int(page) - 1) * int(rows)
        j = (int(page) - 1) * int(rows) + int(rows)
        report_list = MySQLHelper().get_all(CASE_REPORT_LIST, (id,))
        sql_params = [
            'id', 'case_name', 'report_type', 'report_path', 'file_name',
            'update_time', 'username'
        ]
        sub_report = report_list[i:j]
        data = convert_ui_data(sub_report, sql_params)
        total = len(report_list)
        resultdict = {}
        resultdict['code'] = 0
        resultdict['msg'] = ""
        resultdict['count'] = total
        resultdict['data'] = data
        return JsonResponse(resultdict, safe=False)


@login_check
def change_status(request):
    if request.method == "POST":
        param_list, resultdict, msg = ['type', 'id', 'state'], {}, 'ok'
        state, param = params_check(request.body, param_list)
        if not state:
            return JsonResponse({'message': param, 'code': 500})
        type = param.get('type', '')
        id = param.get('id', '')
        state = param.get('state', '')
        if type == 'node':
            UI_Node.objects.filter(is_delete=0, id=id).update(state=state)
        else:
            return JsonResponse({"message": NOT_TYPE, "code": 500})
        return JsonResponse({'message': DEL_SUCCESSS_200, 'code': 200})
    return JsonResponse({"message": NOT_METHMOD, "code": 500})
