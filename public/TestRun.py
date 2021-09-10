# -*-coding:utf-8-*-
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "InterfaceAutoTest.settings")# project_name 项目名称
django.setup()
import re
import unittest
import time
import requests
from BeautifulReport import BeautifulReport
from public.mysqldb import MySQLHelper
from constant import INTERFACE_REPORT_PATH
from public.publicfun import *
from public.interface_request import interface_request
import json
import html
from public.export_report import *
from InterfaceTestManage.models import *
from public.send_email import SendEmail

DEPEND_DATA = {}


class Test(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def setUp(self):
        pass
        # time.sleep(1)
        # print("<p>start!</p>")

    def tearDown(self):
        pass
        # time.sleep(1)
        # print("<p>end!</p>")

    def gettest(self, datas, username, task_id):
        global DEPEND_DATA
        # 前置依赖数据
        task_id = task_id if datas['type'] == 'task' else ""
        self._testMethodDoc = str(datas.get('module_name'))
        self._type = str(datas.get('module_type', ''))
        self._interface_count = str(datas.get('interface_count', ''))
        self._interface_id = str(datas.get('interface_id', ''))
        self._task_id = task_id
        resp_result, resp_code, batch_data, ret = '', 500, '', 2
        try:
            datas['req_path'], DEPEND_DATA = convert_params(datas['req_path'], DEPEND_DATA, datas['project_id'])
            self._req_path = datas['req_path']
            if datas["port"]:
                url = datas['host'] + ":" + datas['port'] + datas['req_path']
            else:
                url = datas['host'] + datas['req_path']
            if datas["req_headers"]:
                datas["req_headers"], DEPEND_DATA = convert_params(datas["req_headers"], DEPEND_DATA, datas['project_id'])
            if datas["req_param"]:
                datas["req_param"], DEPEND_DATA = convert_params(datas["req_param"], DEPEND_DATA, datas['project_id'])
            if datas["req_body"]:
                datas["req_body"], DEPEND_DATA = convert_params(datas["req_body"], DEPEND_DATA, datas['project_id'])
            if datas["except_list"]:
                datas["except_list"], DEPEND_DATA = convert_params(datas["except_list"], DEPEND_DATA, datas['project_id'])
            datas_list = convert_dataDriven(datas)
            for datas in datas_list:
                # 接口请求
                resp_result, _, _, resp_code, _, _, _ = interface_request(datas['req_method'], url, datas["req_param"],
                                                                          datas['req_headers'], datas['req_body'],
                                                                          datas['req_file'], datas['project_id'],
                                                                          datas['subsystem_id'],
                                                                          username, task_id=task_id)
                if datas["wait_time"] != 0:
                    time.sleep(datas["wait_time"])

                # 参数传递
                extract_list = []
                if datas["extract_list"]:
                    batch_data = batch_extract_data(datas["extract_list"], resp_result)
                    for extract in batch_data:
                        extract_param_data = "extract_unit_" + extract["name"]
                        if extract_param_data not in DEPEND_DATA:
                            DEPEND_DATA[extract_param_data] = extract["result"]
                            extract_list.append(
                                html.escape(
                                    "变量名：" + str(extract["name"]) + "， 提取规则：" + str(extract["rule"]) + "， 提取结果：" + str(
                                        extract["result"])))
                # 添加报告中的用例描述
                extract_list = json.dumps(extract_list, ensure_ascii=False) if extract_list else ''
                self._log = [html.escape(str(resp_code)), url, datas["req_method"],
                             html.escape(str(datas["req_param"])), html.escape(datas["req_body"]),
                             html.escape(datas["req_file"]), html.escape(resp_result), extract_list,
                             '']
                if datas["except_list"]:
                    ret, _ = assert_fun(datas["except_list"], resp_result, resp_code)
                    if ret != 2:
                        assert_str = html.escape('断言失败：' + str(ret))
                        raise Exception(assert_str)
                # elif resp_code == 200:
                #     ret = 2
                if datas['type'] == 'task' and datas.get('module_type', '') == 1:
                    task_record(task_id, ret)

        except Exception as e:
            self._req_path = datas['req_path']
            if not resp_result:
                self._log = ['', datas['req_path'], datas["req_method"],
                             html.escape(str(datas["req_param"])), html.escape(datas["req_body"]),
                             html.escape(datas["req_file"]), '', '', str(e)]
            else:
                self._log = [html.escape(str(resp_code)), url, datas["req_method"],
                             html.escape(str(datas["req_param"])), html.escape(datas["req_body"]),
                             html.escape(datas["req_file"]), html.escape(resp_result), extract_list,
                             str(e)]
            if datas.get('module_type', '') == 1:
                ret = 0
                task_record(task_id, ret)
            raise e

    @staticmethod
    def getTestFunc(datas, username, task_id):
        def fun(self):
            self.gettest(datas, username, task_id)

        return fun

    @staticmethod
    def start_test(datas, test_data, suite, username, task_id):
        setattr(test_data, 'test_func_%s' % datas['id'],
                test_data.getTestFunc(datas, username, task_id))  # 通过setattr自动为TestCase类添加成员方法，方法以“test_func_”开头
        # 动态添加测试用例
        suite.addTest(test_data('test_func_%s' % datas['id']))

    def test_suite(suite_datas, test_type, id=None, username=None, report_name=None, project_id=0,
                   report_id=None, report_type=None):
        suite = unittest.TestSuite()
        for i in range(len(suite_datas)):
            case_name = suite_datas[i]['case_name']
            datas = suite_datas[i]
            test = type(case_name, (Test,), {})
            T = test()
            T.start_test(datas, test, suite, username, id)
        now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        if test_type == 'case':
            path = INTERFACE_REPORT_PATH + "case/" + str(project_id) + "/"
            result_file = path + now + '_case_' + id + '_result.html'
        elif test_type == "task":
            path = INTERFACE_REPORT_PATH + "task/" + str(project_id) + "/"
            result_file = path + now + '_task_' + id + '_result.html'
        if not os.path.exists(os.path.join(os.getcwd(), path)):
            os.makedirs(os.path.join(os.getcwd(), path))

        runner = BeautifulReport(suite)
        result_list, result_info = runner.report(description=report_name, filename=result_file, log_path=".")

        # 生成excel
        if test_type == "task":
            new_time = time.time()
            excel_file_name = except_report_excel(id, project_id, report_name, result_info)
            Inte_task.objects.filter(id=id).update(excel_file_name="/" + excel_file_name)
            print(time.time() - new_time)
        # 报告记录
        result_file = '/' + result_file.lstrip('/')
        date_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        count = json.dumps({"sampleCount": result_info["testAll"], "errorCount": result_info["testFail"]})
        if report_type == 1:
            sql = """UPDATE inte_report set task_id='%s',report_path='%s',file_name='%s',username='%s',
                    `job_status`='%s',job_count='%s' WHERE id='%s' """ % (
                int(id), result_file, os.path.split(result_file)[1], username, 0, count, int(report_id))
            MySQLHelper().update(sql)
        else:
            if test_type == "case":
                sql = """update sys_module set report_path='%s', operater='%s' where id=%s""" % (
                    result_file, username, id)
                MySQLHelper().insert(sql)
            elif test_type == "task":
                sql = """INSERT INTO inte_report(create_time, update_time, is_delete, task_id, report_path,
                                 file_name, username, `job_count`, `job_status`, `report_type`) 
                                 VALUES ('%s', '%s', '%d', '%d',  '%s', '%s', '%s' ,'%s', '%d', '%d')
                                """ % (
                    date_time, date_time, 0, int(id), result_file, os.path.split(result_file)[1], username,
                    count, 0, 0)
                MySQLHelper().insert(sql)
        global DEPEND_DATA
        DEPEND_DATA = {}
        if test_type == "task":
            task_name = Inte_task.objects.get(is_delete=0, id=id).task_name
            username = Inte_task.objects.get(is_delete=0, id=id).username
            mail = Sys_user_info.objects.get(username=username, is_delete=0).email
            if mail:
                SendEmail([mail], result_file, task_name).send_email()
        return result_list, result_file


if __name__ == '__main__':
    pass
    # t = {'case1': [{'id': '1', 'interface_name': '登录', 'method': 'POST', 'url': 'http://10.74.194.18/api/login',
    #                 'headers': {
    #                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'},
    #                 'params': {'username': 'admin', 'password': '123456'},
    #                 'case_name': 'Test'}]}
    #
    # Test.test_suite(t, 'task')
