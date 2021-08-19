from mysql_operate_db import MySQLHelper

def conn1():
    # helper = MySQLHelper('10.8.202.194', 3306, 'root', 'bzl123456', 'auto_test')
    # helper = MySQLHelper('127.0.0.1', 3306, 'root', 'bzl123456', 'auto_test')
    helper = MySQLHelper('10.8.72.59', 3306, 'root', 'a123456', 'interface_v05')
    return helper


def conn2():
    # helper = MySQLHelper('10.8.202.194', 3306, 'root', 'bzl123456', 'auto_test_v2.1')
    # helper = MySQLHelper('10.8.72.59', 3306, 'root', 'a123456', 'xy_new')
    helper = MySQLHelper('10.8.72.59', 3306, 'root', 'a123456', 'interface_v05_bak')
    return helper


def escape_str(data, id=None):
    data_str = """"""
    for i in data:
        if i is None:
            i = ""
        else:
            i = str(i)
        data_str += repr(i) + ", "
    sql_str = data_str.rstrip(", ")
    if not id:
        sql_str =  sql_str
    else:
        sql_str = sql_str + ',' + repr(str(id))
    return sql_str


def copy_data_to_data():
    """复制旧数据库到新数据库"""

    # userinfo_info表
    userinfo_info = conn1().get_all(
        "select `id`, `create_time`, `update_time`, `is_delete`, `username`, `email`, `role`, `password`, `status`, `operator` from `userinfo`")
    for i in userinfo_info:
        str_s = escape_str(i)
        try:
            sql = """insert into `sys_user_info`(`id`, `create_time`, `update_time`, `is_delete`, `username`, `email`, `role`, `password`, `state`, `operator`) values (%s)""" % (
                str_s,)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("userinfo_info表完成")

    # user_permission表
    user_permission_info = conn1().get_all(
        "select `id`, `create_time`, `update_time`, `is_delete`, `userid`, `projectid`, `username` from `user_permission`")
    for i in user_permission_info:
        str_s = escape_str(i)
        try:
            sql = """insert into `sys_user_permission`(`id`, `create_time`, `update_time`, `is_delete`, `user_id`, `project_id`, `username`) values (%s)""" % (
                str_s,)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("user_permission表完成")

    # project表
    project_info = conn1().get_all(
        "select `id`, `create_time`, `update_time`, `is_delete`, "
        "`projectName`, `projectdesc`, `username` from `project`")
    for i in project_info:
        str_s = escape_str(i)
        try:
            sql = """insert into `sys_project`(`id`, `create_time`, `update_time`,
            `is_delete`, `project_name`, `project_desc`, `username`) values (%s)""" % (
                str_s,)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("project表完成")

    # dictionary表
    dictionary_info = conn1().get_all("select `id`, `dict_key`, `dict_value` from `dictionary`")
    for i in dictionary_info:
        try:
            str_s = escape_str(i)
            sql = """insert into `sys_dict` (`id`, `dict_key`, `dict_value`) values (%s)""" % (str_s,)
            # print(sql)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("dictionary表完成")

    # subsystem表
    subsystem_info = conn2().get_all(
        "select `id`, `create_time`, `update_time`, `is_delete`, `project_name`, `username` from `sys_project`")
    j = 1
    for i in subsystem_info:
        str_s = escape_str(i)
        try:
            sql = """insert into `sys_subsystem`(`project_id`, `create_time`, `update_time`, `is_delete`, `subsystem_name`, `username`, `id`) values (%s, %s)""" % (
                str_s, str(j))
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
        j = j + 1
    print("subsystem表完成")
    # environment表
    environment_info = conn1().get_all(
        """select `id`, `create_time`, `update_time`, `is_delete`, `env_name`,
         `host`, `port`, `project_id`, `env_desc`, `status`, `username`, `project_id` from `environment`""")
    for i in environment_info:
        try:
            str_s = escape_str(i)
            sql = """insert into `sys_env`(`id`, `create_time`, `update_time`, `is_delete`,
             `env_name`, `host`, `port`, `project_id`, `env_desc`, `state`, `username`, `subsystem_id`) values (%s)""" % (
                str_s,)
            # print(sql)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("environment表完成")

    # interface表
    interface_info = conn1().get_all(
        """select `id`, `create_time`, `update_time`, `is_delete`, `interface_name`,
        `req_path`, `req_method`, `req_headers`, `req_param`, `req_body`,
        `username`, `env_id`, `except_list`, `extract_list`, `status`, `project_id` from `interface` where is_delete=0""")
    for i in interface_info:
        try:
            file_info = conn1().get_all("""select req_file from `interface` where id = %s""", i[0])
            if file_info[0][0]:
                case_file = ''
                for key, value in eval(file_info[0][0]).items():
                    case_file = case_file + '{"param_name":"%s","file_name":"%s","size":""},' % (str(key), str(value))
                case_file = '[%s]' % (case_file.rstrip(','))
            else:
                case_file = ''
            req_file_info = case_file if case_file else ''
            str_s = escape_str(i)
            sql = """insert into `inte_interface`(`id`, `create_time`, `update_time`,
            `is_delete`, `interface_name`, `req_path`, `req_method`, `req_headers`, `req_param`,
            `req_body`, `username`, `env_id`, `except_list`, `extract_list`,
            `state`, `subsystem_id`, `req_file`) values (%s, '%s')""" % (
                str_s, req_file_info)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("interface表完成")

    # sys_module表
    case_info = conn1().get_all(
        """select `id`, `create_time`, `update_time`, `is_delete`, `case_name`, `case_desc`, `username`,
        `interface_list`, case `type` when 'before' then 2 when 'after' then 3 else 1 end `type`,
        `project_id`, `env_id` from `case`""")
    for i in case_info:
        try:
            str_s = escape_str(i)
            sql = """insert into `sys_module` (`id`, `create_time`, `update_time`, `is_delete`,
            `module_name`, `module_desc`, `username`, `case_list`, `module_type`, `subsystem_id`,
             `env_id`) values (%s)""" % (
                str_s,)
            # print(sql)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("sys_module表完成")
    # inte_case表
    case_interface_info = conn1().get_all("""select `id`, `create_time`, `update_time`, `is_delete`, `case_id`,
                case when `remark` != '' then `remark` else `case_name` end `case_name`, `interface_id`,
                 `req_path`, `req_method`, `req_headers`, `req_param`, `req_body`, `is_mock`,
                  `mock_id`, `username`, `run_time`, `except_list`, `extract_list`, `status`, `wait_time` from `case_interface` where is_delete=0""")
    for i in case_interface_info:
        try:
            module_type = conn2().get_all('select module_type from sys_module where id=%s', (i[4],))
            file_info = conn1().get_all("""select req_file from `case_interface` where id = %s""", i[0])
            if file_info[0][0]:
                case_file = ''
                for key, value in eval(file_info[0][0]).items():
                    case_file = case_file + '{"param_name":"%s","file_name":"%s","size":""},' % (str(key), str(value))
                case_file = '[%s]' % (case_file.rstrip(','))
            else:
                case_file = ''
            req_file_info = case_file if case_file else ''
            str_s = escape_str(i, module_type[0][0])
            sql = """insert into `inte_case` (`id`, `create_time`, `update_time`, `is_delete`, `module_id`,
                        `case_name`, `interface_id`, `req_path`, `req_method`, `req_headers`, `req_param`, `req_body`,
                         `is_mock`, `mock_id`, `username`, `run_time`,
                          `except_list`, `extract_list`, `state`,  `wait_time`,`case_type`, `req_file`) values (%s, '%s')""" % (
            str_s, req_file_info)
            # print(sql)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("inte_case表完成")
    # public_param表
    public_param_info = conn1().get_all(
        """select `id`, `create_time`, `update_time`, `is_delete`, `param_name`,
         `param_desc`, `rule`, `state`, `type`, `username`, `dataFormat`,
          `project_id`, `input_params` from `public_param` where `type` != 1""")
    for i in public_param_info:
        str_s = escape_str(i)
        try:
            sql = """insert into `sys_public_param`(`id`, `create_time`, `update_time`, `is_delete`,
             `param_name`, `param_desc`, `rule`, `state`, `param_type`,
             `username`, `data_Format`, `project_id`, `input_params`) values (%s)""" % (
                str_s,)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("public_param表完成")

    # report表
    report_info = conn1().get_all(
        """select `id`, `create_time`, `update_time`, `is_delete`,
         `task_id`, `report_path`, `file_name`, `username` from `report`  where task_id is not null""")
    for i in report_info:
        str_s = escape_str(i)
        try:
            sql = """insert into `inte_report`(`id`, `create_time`, `update_time`,
            `is_delete`, `task_id`, `report_path`, `file_name`, `username`) values (%s)""" % (
                str_s,)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("report表完成")

    # sql_env表
    sql_env_info = conn1().get_all(
        """select `id`, `create_time`, `update_time`, `is_delete`,
         `project_id`, `type`, `ip`, `env_name`, `env_port`, `env_desc`,
          `user`, `password`, `dbname`, `username` from `sql_env`""")
    for i in sql_env_info:
        str_s = escape_str(i)
        try:
            sql = """insert into `sys_db_env`(`id`, `create_time`, `update_time`, `is_delete`,
            `project_id`, `db_type`, `env_ip`, `env_name`, `env_port`,
             `env_desc`, `user`, `password`, `dbname`, `username`) values (%s)""" % (
                str_s,)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("sql_env表完成")

    # sql_statement表
    sql_statement_info = conn1().get_all("""select `id`, `create_time`, `update_time`, `is_delete`,
     `env_id`, `sql_name`, `sql`, `status`, `result`, `username` from `sql_statement`""")
    for i in sql_statement_info:
        str_s = escape_str(i)
        try:
            sql = """insert into `sys_db_sqldetail`(`id`, `create_time`,
            `update_time`, `is_delete`, `env_id`, `sql_name`, `sql`, `state`, `result`, `username`) values (%s)""" % (
                str_s,)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("sql_statement表完成")

    # task表
    task_info = conn1().get_all(
        """select `id`, `create_time`, `update_time`, `is_delete`,
        `task_name`, `task_desc`, `username`, `interface_list`,
        `execute_result`, `cron`, `state`, `project_id` from `task` where is_delete=0""")
    for i in task_info:
        str_s = escape_str(i)
        if i[7]:
            case_dici_str = '{"' + str(i[11]) + '":"' + str(i[7]) + '"}'
        else:
            case_dici_str = ''
        try:
            sql = """insert into `inte_task`(`id`, `create_time`, `update_time`, `is_delete`,
            `task_name`, `task_desc`, `username`, `case_list`, `execute_result`, `cron`, `state`,
             `project_id`, `case_dict`) values (%s, '%s')""" % (
                str_s, case_dici_str)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("task表完成")

    # task_interface表
    task_interface_info = conn1().get_all(
        """select `id`, `create_time`, `update_time`, `is_delete`, `task_id`, `case_interface_id`,
        `case_name`, `req_path`, `req_method`, `req_headers`, `req_param`, `req_body`,
         `extract_list`, `except_list`, `is_mock`, `mock_id`, `run_time`, `username`, `status`, `wait_time` from `task_interface` where is_delete=0""")
    for i in task_interface_info:
        try:
            file_info = conn1().get_all("""select req_file from `task_interface` where id = %s""", i[0])
            if file_info[0][0]:
                case_file = ''
                for key, value in eval(file_info[0][0]).items():
                    case_file = case_file + '{"param_name":"%s","file_name":"%s","size":""},' % (str(key), str(value))
                case_file = '[%s]' % (case_file.rstrip(','))
            else:
                case_file = ''
            req_file_info = case_file if case_file else ''
            str_s = escape_str(i)
            sql = """insert into `inte_task_case`(`id`, `create_time`, `update_time`, `is_delete`, `task_id`,
             `case_id`, `case_name`, `req_path`, `req_method`, `req_headers`, `req_param`, `req_body`,
              `extract_list`, `except_list`, `is_mock`, `mock_id`, `run_time`, `username`, `state`, `wait_time`,`req_file`) values (%s, '%s')""" % (
                str_s, req_file_info)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("task_interface表完成")

    # inte_extract表
    inte_extract_info = conn1().get_all(
        "select `id`, `create_time`, `update_time`, `is_delete`, `param_name`,"
        " `param_desc`, `rule`, `username`, `dataFormat`, `project_id` from `public_param` where `type` = 1")
    for i in inte_extract_info:
        str_s = escape_str(i)
        try:
            sql = """insert into `inte_extract`(`id`, `create_time`, `update_time`,
            `is_delete`, `param_name`, `param_desc`, `rule`, `username`, `data_Format`, `project_id`) values (%s)""" % (
                str_s,)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("inte_extract表完成")

    # inte_task_record表
    inte_task_record_info = conn1().get_all("""select t.task_id, i.create_time, i.create_time,
        sum(case when i.execute_status=0 then 1 else 0 end) 'fail_count',
        sum(case when i.execute_status=1 then 1 else 0 end) 'assert_count',
        sum(case when i.execute_status=2 then 1 else 0 end) 'success_count', count(i.id)
        from interface_record i
				left join task_record t on i.task_record_id=t.id
        where i.task_record_id is not null
        group by i.task_record_id, date_format(i.create_time,'%Y-%m-%d')""")
    for i in inte_task_record_info:
        str_s = escape_str(i)
        try:
            sql = """insert into `inte_task_record`(`task_id`, `create_time`, `update_time`,
            `fail_count`, `assert_count`, `success_count`, `execute_count`, `is_delete`) values (%s, 0)""" % (
                str_s,)
            conn2().insert(sql)
        except Exception as e:
            # print(e)
            print(i[0])
            print(sql)
    print("inte_task_record表完成")



copy_data_to_data()
# def copy_data():
#
#
# copy_data()

