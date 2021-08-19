# coding:utf-8
from mysql_operate_db import MySQLHelper
import json


def conn():
    helper = MySQLHelper('10.8.202.194', 3306, 'root', 'bzl123456', 'auto_test_v2.1')
    # helper = MySQLHelper('127.0.0.1', 3306, 'root', '123456', 'auto_test')
    # helper = MySQLHelper('10.8.72.59', 3306, 'root', 'a123456', 'xy_new')
    return helper


# 更新任务中用例列表的结构顺序
def update_db():
    result = conn().get_all('select id,case_list from inte_task')
    for i in result:
        id = i[0]
        if id in [76]:  # , 85, 86, 88, 89, 94
            if i[1]:
                task_str = (','.join(list(eval(i[1]).values()))).strip(',')
                print(id)
                sql = """select inte_case.id from inte_case where inte_case.id in (%s) and case_type =%s"""
                # ('正常用例', 1), ('前置条件用例', 2), ('后置条件用例', 3)
                before_sql = sql % (task_str, 2)
                before_list = conn().get_all(before_sql)
                before_list = (','.join([str(x[0]) for x in before_list])).strip(',')
                # print(before_list)
                case_sql = sql % (task_str, 1)
                case_list = conn().get_all(case_sql)
                case_list = (','.join([str(x[0]) for x in case_list])).strip(',')

                # print(case_list)
                after_sql = sql % (task_str, 3)
                after_list = conn().get_all(after_sql)
                after_list = (','.join([str(x[0]) for x in after_list])).strip(',')
                # print(after_list)
                case_dict = json.dumps({"before_list": before_list, "case_list": case_list, "after_list": after_list})
                conn().update("update inte_task set case_list='%s' where id=%s" % (case_dict, i[0]))


def update_task_env():
    case_list = []
    result = conn().get_all('select id,case_id, env_id from inte_task_case')
    for i in result:
        if not i[2]:
            case_id = i[1]
            sql = """select env_id from sys_module left join inte_case on sys_module.id=inte_case.module_id where inte_case.id=%s""" % case_id
            env_id = conn().get_all(sql)
            print(i[0])
            if not env_id:
                case_list.append(i[0])
            else:
                conn().update("update inte_task_case set env_id=%s where id=%s" % (env_id[0][0], i[0]))

    print(case_list)
    print(len(case_list))


if __name__ == "__main__":
    # 更新任务中用例列表的结构顺序
    update_db()
    # 更新任务用例的单条用例环境
    # update_task_env()
