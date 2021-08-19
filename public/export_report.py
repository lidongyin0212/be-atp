# coding:utf-8
import pymysql
import os
import time
from public.readexcel import *
from public.writeexcel import *
from public.mysqldb import *
from InterfaceTestManage.utils.sql_manager import *
import xlwt

def except_report_excel(task_id, project_id, report_name, result_info):
    path = 'static/excel_report/' + str(project_id) + '/'
    file_name = path + report_name + '.xls'
    if not os.path.exists(os.path.join(os.getcwd(), path)):
        os.makedirs(path)
    subsystem_info = MySQLHelper().get_all(
        "select case_dict,project_name from inte_task left join sys_project on sys_project.id=inte_task.project_id where inte_task.id=%s" % (
            task_id,))
    subsystem_list = ",".join(set(eval(subsystem_info[0][0]).keys()))
    sql = TASK_CASE_INTERFACE_DATA % (task_id, subsystem_list)
    task_info = MySQLHelper().get_all(sql)
    result_dict = {}
    for test_result in result_info['testResult']:
        if test_result['type'] == '1':
            if test_result['status'] == '成功':
                if str(test_result['interface_id']) not in result_dict:
                    result_dict[str(test_result['interface_id'])] = {"result": "成功", "msg": '-'}
            else:
                result_dict[str(test_result['interface_id'])] = {"result": "失败", "msg": test_result['log'][-1]}

    workbook = xlwt.Workbook(encoding='utf-8')
    worksheet = workbook.add_sheet('测试结果')
    worksheet.write(0, 0, '项目名称')
    worksheet.write(1, 0, '报告名称')
    worksheet.write(2, 0, '项目接口总数')
    worksheet.write(3, 0, '报告接口总数')
    worksheet.write(4, 0, '用例数')
    worksheet.write(5, 0, '接口覆盖率')
    worksheet.write(6, 0, '成功用例个数')
    worksheet.write(7, 0, '失败用例个数')
    worksheet.write(8, 0, '开始时间')
    worksheet.write(9, 0, '运行时间')

    worksheet.write(0, 1, subsystem_info[0][1])
    worksheet.write(1, 1, report_name)
    worksheet.write(2, 1, str(result_info['all_interface_count']))
    worksheet.write(3, 1, str(result_info['interface_count']))
    worksheet.write(4, 1, str(result_info['testAll']))
    worksheet.write(5, 1, result_info['interface_coverage'])
    worksheet.write(6, 1, str(result_info['testPass']))
    worksheet.write(7, 1, str(result_info['testFail']))
    worksheet.write(8, 1, result_info['beginTime'])
    worksheet.write(9, 1, result_info['totalTime'])

    worksheet.write(11, 0, "序号")
    worksheet.write(11, 1, "接口名称")
    worksheet.write(11, 2, "请求路径")
    worksheet.write(11, 3, "用例数")
    worksheet.write(11, 4, "结果")
    worksheet.write(11, 5, "原因")

    for i in range(len(task_info)):
        worksheet.write(12 + i, 0, i + 1)
        worksheet.write(12 + i, 1, task_info[i][0])
        worksheet.write(12 + i, 2, task_info[i][1])
        worksheet.write(12 + i, 3, task_info[i][2])
        if str(task_info[i][3]) in result_dict:
            worksheet.write(12 + i, 4, result_dict[str(task_info[i][3])]["result"])
            worksheet.write(12 + i, 5, result_dict[str(task_info[i][3])]["msg"])
        else:
            worksheet.write(12 + i, 4, "-")
            worksheet.write(12 + i, 5, "-")
    workbook.save(file_name)
    return file_name
