# coding:utf-8
from mysql_operate_db import MySQLHelper


def conn():
    # helper = MySQLHelper('10.8.202.194', 3306, 'root', 'bzl123456', 'auto_test')
    # helper = MySQLHelper('127.0.0.1', 3306, 'root', '123456', 'auto_test')
    helper = MySQLHelper('10.8.72.59', 3306, 'root', 'a123456', 'auto_test')
    return helper


def add_public_case():
    result = conn().get_all("select id, projectName from project where is_delete=0")
    for i in result:
        print(i)
        sql1 = "insert `case` (case_name, project_id,`type`, is_delete, username, create_time, update_time, interface_list) " \
               "value ('%s', '%s' ,'%s', 0,'%s','%s', '%s', '')" % (
                   '前置条件', i[0], 'before', 'admin', '2000-01-01 00:00:00', '2000-01-01 00:00:00')
        conn().insert(sql1)
        sql2 = "insert `case` (case_name, project_id,`type`, is_delete, username, create_time, update_time, interface_list) " \
               "value ('%s', '%s' ,'%s', 0,'%s','%s', '%s', '')" % (
                   '后置条件', i[0], 'after', 'admin', '2001-01-01 00:00:00', '2000-01-01 00:00:00')
        conn().insert(sql2)


add_public_case()
