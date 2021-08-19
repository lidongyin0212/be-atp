# coding:utf-8
from mysql_operate_db import MySQLHelper


def conn():
    helper = MySQLHelper('10.8.72.59', 3306, 'root', 'a123456', 'auto_test')
    return helper


def convert_data(ret, params, flag=False):
    data_list = []
    for info in ret:
        count = 0
        data_dict = {}
        for item1 in info:
            if flag and isinstance(item1, str):
                if params[count] != 'except_list':
                    item1 = item1.replace("\\\\\\\\", "\\\\")

            data_dict[params[count]] = item1
            count += 1
        data_list.append(data_dict)
    return data_list


def update_if():
    sql = """select GROUP_CONCAT(case_interface.id) as ids, case_id from case_interface where is_delete = 0 group by case_interface.case_id"""
    sql_param = ['ids', 'case_id']
    interface_list = convert_data(conn().get_all(sql, ), sql_param)
    update_sql = """update `case` set interface_list= %s where id = %s"""
    for i in interface_list:
        try:
            conn().update(update_sql, (i['ids'], i['case_id']))
        except Exception as e:
            print(e)


if __name__ == "__main__":
    update_if()
