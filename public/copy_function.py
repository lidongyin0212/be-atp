# -*- coding: utf-8 -*-
# @Time    : $[DATA] $[TIME]
# @Author  : zhang lin
import json
import time
from InterfaceTestManage.utils.sql_manager import *
from InterfaceTestManage.models import *
from public.mysqldb import MySQLHelper
from public.publicfun import convert_data

# 获取当前系统时间
copy_get_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))


# 树形图处理函数
def list_to_tree1(module_data):
    res = {}
    for i, v in enumerate(module_data):
        v["parent_id"] = v["parent_id"] if v["parent_id"] else 0
        res.setdefault(v["id"], v)
        res.setdefault(v["parent_id"], {}).setdefault("children", []).append(v)
    return res[0]["children"]


'''复制子系统'''


def copy_subsystem(subsystem_id, username):
    '''
    :param subsystem_id: 系统 id
    :return:
    '''
    add_subsystem_id = ""
    try:
        subsystem_sql_param = ['subsystem_name', 'subsystem_desc', 'username', 'project_id']
        # 查询子系统
        subsystem_list = convert_data(MySQLHelper().get_all(SUBSYSTEM_SQL, subsystem_id), subsystem_sql_param)
        try:
            for i in subsystem_list:  # 插入子系统
                subsystem_name = i['subsystem_name'] + '_复制'
                if len(subsystem_name) > 20:
                    return "名称超长"
                exist = Sys_subsystem.objects.filter(subsystem_name=subsystem_name, is_delete=0)
                if exist:
                    return "名称重复"
                add_subsystem_id = Sys_subsystem.objects.create(create_time=copy_get_time, update_time=copy_get_time,
                                                                is_delete=0,
                                                                subsystem_name=subsystem_name,
                                                                subsystem_desc=i['subsystem_desc'],
                                                                username=username, project_id=i['project_id']).id
        except:
            return "子系统复制失败!"
        # 复制环境并返回环境id字典
        env_sql_param = ['id', 'env_name', 'env_desc', 'host', 'port', 'project_id', 'state', 'username',
                         'subsystem_id']
        env_list = convert_data(MySQLHelper().get_all(EVN_copy_SQL, subsystem_id), env_sql_param)
        env_dict = {} # key：旧id   value：新id
        try:
            for i in env_list:
                env_name = i["env_name"] + '_复制'
                nwe_envId = Sys_env.objects.create(
                    create_time=copy_get_time, update_time=copy_get_time, is_delete=0, env_name=env_name,
                    env_desc=i["env_desc"], host=i["host"], port=i["port"], project_id=i["project_id"],
                    state=i["state"], creator=username,
                    username=username, subsystem_id=add_subsystem_id).id
                env_dict[str(i["id"])] = nwe_envId
        except:
            Sys_subsystem.objects.filter(id=add_subsystem_id).update(is_delete=1)  # 复制失败时删除复制后的子系统
            return "环境复制失败！"

        # 模块
        module_sql_param = ['id', 'module_name', 'module_desc', 'module_type', 'parent_id', 'subsystem_id', 'env_id',
                            'case_list', 'sub_module_list', 'username', 'operater']
        module_list_a = convert_data(MySQLHelper().get_all(MODULE_SQL, subsystem_id), module_sql_param)
        module_list = list_to_tree1(module_list_a)  # 树形图

        # 复制接口并返回新旧接口id字典
        interface_sql_param = ['id', 'interface_name', 'req_path', 'req_method', 'req_headers', 'req_param', 'req_body',
                               'req_file', 'extract_list','except_list', 'state', 'excute_result', 'env_id', 'username',
                               'subsystem_id', 'project_id']
        interface_list = convert_data(MySQLHelper().get_all(INTERFACE_SQL, subsystem_id), interface_sql_param)
        interface_dict = {}
        try:
            for i in interface_list:
                new_id = env_dict[str(i['env_id'])]
                id = Inte_interface.objects.create(create_time=copy_get_time, update_time=copy_get_time, is_delete=0,
                                                   interface_name=i['interface_name'],req_path=i['req_path'],
                                                   req_method=i['req_method'],req_headers=i['req_headers'],
                                                   req_param=i['req_param'], req_body=i['req_body'],
                                                   req_file=i['req_file'],extract_list=i['extract_list'],
                                                   except_list=i['except_list'],state=i['state'],
                                                   excute_result=i['excute_result'], env_id=new_id,
                                                   project_id=i['project_id'],username=username,
                                                   creator=username, subsystem_id=add_subsystem_id).id
                interface_dict[str(i['id'])] = id
        except:
            Sys_subsystem.objects.filter(id=add_subsystem_id).update(is_delete=1)  # 复制失败时删除复制后的子系统
            return "接口复制失败！"

        # 插入模块和用例
        insert_module(add_subsystem_id, module_list, username, env_dict, interface_dict)
        return "复制成功"
    except Exception as e:
        print(e)
        Sys_subsystem.objects.filter(id=add_subsystem_id).update(is_delete=1)  # 复制失败时删除复制后的子系统
        return "复制失败:%s" % e

# 插入模块与子模块
def insert_module(add_subsystem_id, module_list, username, env_dict, interface_dict, parent_id=None):
    '''
    :param add_subsystem_id: 复制后的系统id
    :param module_list: 树形图列表
    :param new_interface_id: 复制后的接口id
    :param parent_id: 上级id
    :return:
    '''
    for i in module_list:
        if i['env_id'] == "" or i['env_id'] == None:
            env_id = None
        else:
            env_id = env_dict[str(i['env_id'])] # 通过旧id 获取新id
        if 'children' in i:  # 判断有子模块
            id = Sys_module.objects.create(create_time=copy_get_time, update_time=copy_get_time, is_delete=0,
                                           module_name=i['module_name'],
                                           module_desc=i['module_desc'], module_type=i['module_type'],
                                           parent_id=parent_id,
                                           subsystem_id=add_subsystem_id, env_id=env_id, case_list=i['case_list'],
                                           sub_module_list=i['sub_module_list'], username=username,
                                           operater=i['operater']
                                           ).id
            # 调用本身
            insert_module(add_subsystem_id, i['children'], username, env_dict, interface_dict, id)
        else:  # 判断非子模块
            id = Sys_module.objects.create(create_time=copy_get_time, update_time=copy_get_time, is_delete=0,
                                           module_name=i['module_name'],
                                           module_desc=i['module_desc'], module_type=i['module_type'],
                                           parent_id=parent_id,
                                           subsystem_id=add_subsystem_id, env_id=env_id,
                                           case_list=i['case_list'],
                                           sub_module_list=i['sub_module_list'], username=username,
                                           operater=i['operater']
                                           ).id
        # 判断模块是否绑定用例
        if not i['case_list']:
            continue
        else:
            # 插入用例并返回inte_case.id
            case_list = inte_case_add(i['case_list'], id, username, interface_dict)
            case_list = ','.join([str(i) for i in case_list])
            # 更新module.case_list
            Sys_module.objects.filter(id=id).update(case_list=case_list)


# 插入用例
def inte_case_add(case_list, module_id, username, interface_dict):
    '''
    :param case_list:树形图中的case_list
    :param module_id: 复制后的模块id
    :return: id_list：复制后的用例id集，list类型
    '''
    case_sql_param = ['id', 'case_name', 'req_path', 'req_method', 'req_headers', 'req_param', 'req_body', 'req_file',
                      'extract_list', 'except_list', 'is_mock', 'mock_id', 'run_time', 'state', 'excute_result',
                      'interface_id', 'module_id',
                      'username','case_type' ]
    sql = INTE_CASE_SQL % (case_list, case_list)
    cese_list = convert_data(MySQLHelper().get_all(sql),case_sql_param)
    id_list = []
    for i in cese_list:
        mock_id = i['mock_id'] if i['mock_id'] else None
        new_interface_id = interface_dict[str(i['interface_id'])]  # 通过旧接口ID 获取新的接口ID
        new_subsystem_id = Inte_interface.objects.get(id=new_interface_id).subsystem_id
        extract_list = i['extract_list']
        extract_param = ['param_name', 'param_desc', 'rule', 'data_format', 'project_id', 'subsystem_id']
        sql = EXTRACT_SQL % extract_list
        extract_list = convert_data(MySQLHelper().get_all(sql), extract_param)
        for j in extract_list:
            extract_id = Inte_extract.objects.create(
                create_time=copy_get_time, update_time=copy_get_time, is_delete=0, param_name=j["param_name"],
                param_desc=j['param_desc'], rule=j['rule'], data_format=j['data_format'], project_id=j['project_id'],
                subsystem_id=new_subsystem_id, username=username
            ).id
        id = Inte_case.objects.create(
            create_time=copy_get_time, update_time=copy_get_time, is_delete=0, case_name=i['case_name'],
            req_path=i['req_path'],
            req_method=i['req_method'], req_headers=i['req_headers'], req_param=i['req_param'], req_body=i['req_body'],
            req_file=i['req_file'], extract_list=extract_id, except_list=i['except_list'], is_mock=i['is_mock'],
            mock_id=mock_id, run_time=i['run_time'], state=i['state'], excute_result=i['excute_result'],
            interface_id=new_interface_id, module_id=module_id, username=username, creator=username,
            case_type=i["case_type"]
        ).id
        id_list.append(id)
    return id_list


'''任务复制'''


def copy_task(task_id, username):
    '''
    :param task_id: 任务id
    :param username: 操作人
    '''
    new_task_id = 0
    task_sql_param = ['task_name', 'task_desc', 'case_list', 'case_dict', 'execute_result', 'cron', 'project_id',
                      'state']
    task_cese_sql_param = ['case_id', 'case_name', 'req_path', 'req_method', 'req_headers',
                           'req_param', 'req_body', 'req_file', 'extract_list', 'except_list', 'is_mock',
                           'mock_id', 'run_time', 'state', 'env_id', 'excute_result']
    # 根据任务id 查询任务表
    task_list = convert_data(MySQLHelper().get_all(TASK_SQL, task_id), task_sql_param)
    if not task_list:
        return "任务没有用例", new_task_id
    try:
        for i in task_list:
            task_name = i['task_name'] + "_复制"
            if len(task_name) > 20:
                return "名称超长", new_task_id
            exist = Inte_task.objects.filter(task_name=task_name, is_delete=0)
            if exist:
                return "名称重复", new_task_id
            try:
                new_task_id = Inte_task.objects.create(create_time=copy_get_time, update_time=copy_get_time,
                                                       is_delete=0,
                                                       task_name=task_name, task_desc=i['task_desc'],
                                                       case_list=i['case_list'], case_dict=i['case_dict'],
                                                       execute_result=i['execute_result'],
                                                       cron=i['cron'], project_id=i['project_id'], state=i['state'],
                                                       username=username, creator=username).id
            except:
                return "任务复制失败！", new_task_id
            # case_list = json.loads(i['case_list'])  # str -- dict
            case_list = eval(i['case_list']) # str -- dict
            get_case_list = []
            for key in case_list:
                list = case_list[key]
                get_case_list.append(list)

            get_list = ",".join([str(i) for i in get_case_list if str(i)])
            sql = TASK_CASE_SQL % (task_id, get_list, get_list)
            task_case_list = convert_data(MySQLHelper().get_all(sql),task_cese_sql_param)
            try:
                # 遍历正常用例
                for j in task_case_list:
                    mock_id = j["mock_id"] if j["mock_id"] else None
                    Inte_task_case.objects.create(
                        create_time=copy_get_time, update_time=copy_get_time, is_delete=0,
                        task_id=new_task_id, case_id=j["case_id"], case_name=j["case_name"], req_path=j["req_path"],
                        req_method=j["req_method"], req_headers=j["req_headers"], req_param=j["req_param"],
                        req_body=j["req_body"], req_file=j["req_file"], extract_list=j["extract_list"],
                        except_list=j["except_list"], is_mock=j["is_mock"], mock_id=mock_id, run_time=j["run_time"],
                        state=j["state"], env_id=j["env_id"], excute_result=j["excute_result"], username=username,
                        creator=username
                    )
            except:
                Inte_task.objects.filter(id=new_task_id).update(is_delete=1)
                return "任务用例复制失败！", new_task_id
        return "复制成功", new_task_id
    except Exception as e:
        print(e)
        return e

# if __name__ == '__main__':
#
#     # copy_task(1, 'zhanglin')
#
#     copy_subsystem(1, 'zhanglin')
