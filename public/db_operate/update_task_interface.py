# coding:utf-8
from mysql_operate_db import MySQLHelper


def conn():
    # helper = MySQLHelper('10.8.202.194', 3306, 'root', 'bzl123456', 'auto_test')
    helper = MySQLHelper('127.0.0.1', 3306, 'root', '123456', 'auto_test')
    return helper


def convert_data(ret, params, flag=False):
    data_list = []
    for info in ret:
        count = 0
        data_dict = {}
        for item1 in info:
            if item1 is None:
                item1 = ''
            if flag and isinstance(item1, str):
                if params[count] != 'except_list':
                    item1 = item1.replace("\\\\\\\\", "\\\\")
            data_dict[params[count]] = item1
            count += 1
        data_list.append(data_dict)
    return data_list


def convert_quot(data):
    datas = data.replace("\"", "\\\"")
    return datas


def update_if():
    task_sql = """select id, interface_list, username, create_time from task"""
    task_sql_param = ['id', 'interface_list', 'username', 'create_time']
    task_list = convert_data(conn().get_all(task_sql, ), task_sql_param)
    for i in task_list:
        sql = """select ci.id, ci.interface_id, ci.case_id, case when ci.remark!="" then ci.remark else i.interface_name
         end, c.project_id, c.env_id, ci.req_path, ci.req_method, ci.req_headers, ci.req_param, ci.req_body, 
         ci.req_file, ci.extract_list, ci.except_list, ci.run_time
                from case_interface as ci
                left join `case` as c on ci.case_id=c.id
                left join interface as i on ci.interface_id=i.id
                where ci.is_delete = 0 and ci.id in (%s)""" % (i.get('interface_list'))
        if i.get('interface_list'):
            sql_param = ['id', 'interface_id', 'case_id', 'case_name', 'project_id', 'env_id', 'req_path', 'req_method',
                         'req_headers', 'req_param', 'req_body', 'req_file', 'extract_list', 'except_list', 'run_time']
            interface_list = convert_data(conn().get_all(sql), sql_param)

            for j in interface_list:
                insert_sql = """insert into `task_interface`(case_interface_id, case_id, case_name, project_id, env_id, 
                req_path, req_method, req_headers, req_param, req_body, req_file, extract_list, except_list, run_time, 
                username, task_id, is_mock, is_delete, create_time, update_time) values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', "%s", "%s", '%s', '%s', '%s', 0, 0, '%s', '%s')""" % (
                    j['id'], j['case_id'], j['case_name'], j['project_id'],
                    j['env_id'], j['req_path'], j['req_method'],
                    convert_quot(j['req_headers']), convert_quot(j['req_param']), convert_quot(j['req_body']),
                    convert_quot(j['req_file']), convert_quot(j['extract_list']), convert_quot(j['except_list']),
                    j['run_time'], i['username'], i['id'], i['create_time'], i['create_time'])
                try:
                    conn().insert(insert_sql)
                except Exception as e:
                    insert_sql = """insert into `task_interface`(case_interface_id, case_id, case_name, project_id, env_id, 
                                    req_path, req_method, req_headers, req_param, req_body, req_file, extract_list, except_list, run_time, 
                                    username, task_id, is_mock, is_delete, create_time, update_time) values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', "%s", '%s', '%s', '%s', '%s', 0, 0, '%s', '%s')""" % (
                        j['id'], j['case_id'], j['case_name'], j['project_id'],
                        j['env_id'], j['req_path'], j['req_method'],
                        convert_quot(j['req_headers']), convert_quot(j['req_param']), convert_quot(j['req_body']),
                        convert_quot(j['req_file']), convert_quot(j['extract_list']), convert_quot(j['except_list']),
                        j['run_time'], i['username'], i['id'], i['create_time'], i['create_time'])
                    conn().insert(insert_sql)

                    print("i:" + str(i['id']))
                    print("j:" + str(j['id']))
                    print(sql)
                    print(e)


if __name__ == "__main__":
    update_if()
