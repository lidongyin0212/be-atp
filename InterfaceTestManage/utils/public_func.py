import time


# from ..models import Sys_user_info
# from django.http import HttpResponseRedirect, JsonResponse
# from constant import NOT_PERMISSION
# from .sql_manager import GET_PERSON_PROJECT
# from public.mysqldb import MySQLHelper

def get_time():
    return time.strftime(
        '%Y-%m-%d %H:%M:%S', time.localtime(time.time()))


# # 增删改权限校验
# def operate_check(func):
#     def wrapper(request, *args, **kwargs):
#         username = request.session.get('username')
#         if not username:
#             return HttpResponseRedirect('/login')
#
#         userinfo = UserInfo.objects.filter(username=username)
#         userinfo.update(update_time=get_time())
#         project_id = eval(request.body).get("project_id", "")
#         if not project_id:
#             context = {'message': "参数:%s 错误" % "project_id", 'code': 500}
#             return JsonResponse(context)
#         result = MySQLHelper().get_all(GET_PERSON_PROJECT, (username, project_id))
#         if not result:
#             context = {'message': NOT_PERMISSION, 'code': 500}
#             return JsonResponse(context)
#         return func(request, *args, **kwargs)
#     return wrapper
#
# 用户树形数据处理
# ((1, 1, 'admin', '人脸', 1), (8, None, '123456', '', 2), (9, None, '123', '', 3))
def handle_tree_data(permission_data):  # , checkdata=None
    data = {}
    for user in permission_data:
        sub_data = {}
        if str(user[0]) not in data:
            sub_data["title"] = user[2]
            if user[3]:
                sub_data["children"] = [{"title": user[3], "id": user[1]}]
            else:
                sub_data["children"] = []
            data[str(user[0])] = sub_data
        else:
            if user[3]:
                data[str(user[0])]["children"].append({"title": user[3], "id": user[1]})
    user_tree = []
    for value in data.values():
        user_tree.append(value)
    return user_tree


# 用例树形数据处理
def handle_case_data(case_data, module_id):
    '''
    :param case_data: mysql查询结果
    :param module_id: 模块id
    :return:0：模块id 1：用例id 2：模块名称 3：用例名称 4：模块删除 5：模块列表 6：上级id
    '''
    data = {}
    for user in case_data:
        sub_data = {}
        if str(user[0]) not in data:
            sub_data["title"] = user[2]  # 模块名称
            sub_data["id"] = user[0]  # 模块id
            # 判断用例是否为前置用例或者后置用例
            sub_data["level"] = "1" if user[5] else "2"
            if module_id:  # 模块id存在
                if int(module_id) == user[0]:
                    sub_data['spread'] = True
            if user[3] and not user[4]:  # 用例名称存在 且 未删除
                sub_data["children"] = [{"title": user[3], "id": user[1], 'level': "3"}]
            else:
                sub_data["children"] = []
            data[str(user[0])] = sub_data
        else:
            if user[3] and not user[4]:  # 用例名称存在 且 未删除
                data[str(user[0])]["children"].append({"title": user[3], "id": user[1], 'level': "3"})
    case_tree = []
    for value in data.values():
        case_tree.append(value)
    print(case_tree)
    return case_tree


# 列表数据转化为树形图
def list_to_tree(module_data):
    res = {}
    for i, v in enumerate(module_data):
        v["parent_id"] = v["parent_id"] if v["parent_id"] else 0
        res.setdefault(v["id"], v)
        res.setdefault(v["parent_id"], {}).setdefault("children", []).append(v)
    return res[0]["children"]

# 递归拼接用例id
def get_str(case_str, module_list):
    for item in module_list:
        case_str += ',' + item['case_list']
        case_str = case_str.strip(',')
        if 'children' in item:
            module_list = item['children']
            case_str = get_str(case_str, module_list)
    return case_str

# 删除任务用例字典时使用
def check_taks_case_dict(case_id, str_dict):
    """
    :param case_id: 需要删除的用例id
    :param str_dict: 任务用例id字典
    :return:
    """
    for i, v in enumerate(str_dict):
        case_list = str_dict[v].split(',')
        if case_id in case_list:
            case_list.remove(case_id)
            if case_list:
                str_dict[v] = ','.join(case_list).strip(',')
            else:
                del str_dict[v]
    return str_dict


if __name__ == '__main__':
    module_data = [{'id': 5, 'title': '4444', 'parent_id': '', 'level': 2},
                   {'id': 6, 'title': '555', 'parent_id': 5, 'level': 2},
                   {'id': 7, 'title': '666', 'parent_id': 5, 'level': 2},
                   {'id': 8, 'title': '777', 'parent_id': '', 'level': 2},
                   {'id': 9, 'title': '88', 'parent_id': 7, 'level': 2},
                   {'id': 10, 'title': '88', 'parent_id': 9, 'level': 2},
                   {'id': 11, 'title': '12', 'parent_id': 5, 'level': 2},
                   {'id': 12, 'title': '213123', 'parent_id': 8, 'level': 2},
                   {'id': 13, 'title': '1112', 'parent_id': '', 'level': 2},
                   {'id': 14, 'title': '123', 'parent_id': '', 'level': 2},
                   {'id': 15, 'title': '1231', 'parent_id': '', 'level': 2}]
    print(list_to_tree(module_data))
