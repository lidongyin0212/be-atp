# -*-coding:utf-8-*-
import os
import re
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains  # 引入actionchains类
from selenium.webdriver.common.keys import Keys
from time import ctime
from selenium.webdriver.support.select import Select
import time
from .BeautifulReport import BeautifulReport
from public.mysqldb import MySQLHelper
from constant import UI_REPORT_PATH
from .page import *
import json


class Test(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)

    def setUp(self):
        pass
        # time.sleep(1)
        # print("<p>start!</p>")

    def tearDown(self):
        self.page.quit()
        # pass
        # time.sleep(1)
        # print("<p>end!</p>")

    def gettest(self, datas):
        step_list = ''
        for data in datas:
            if data['extract_param']:
                step_list += """%s=""" % data['extract_param']
            if data['step_element'] == 'browser':
                step_list += """self.page = Page(browser_type=%s).%s(%s) \n""" % (
                    data['element_location'], data['step_action'], data['step_params'])
            elif data['step_element'] == 'time':
                step_list += """time.%s(%s) \n""" % (data['step_action'], data['step_params'])
            elif data['step_element'] == 'page':
                if data['step_action'] in list(
                        filter(lambda m: not m.startswith("__") and not m.endswith("__") and callable(getattr(Page, m)),
                               dir(Page))):
                    step_list += """self.page.%s(%s) \n""" % (data['step_action'], data['step_params'])
                elif data['step_action'][:5] == 'assert':
                    step_list += """self.%s(%s)""" % (data['step_action'], data['step_params'])
                else:
                    step_list += """self.page.driver.%s(%s) \n""" % (
                        data['step_action'], data['step_params'])
            else:
                step_list += """self.page.%s(%s).%s(%s) \n""" % (data['step_element'], data['element_location'],
                                                                 data['step_action'], data['step_params'])

        print(step_list)
        exec(step_list)

    @staticmethod
    def getTestFunc(datas):
        def fun(self):
            self.gettest(datas)

        return fun

    @staticmethod
    def start_test(datas, test_data, suite, id=None):
        setattr(test_data, 'test_func_%s' % id,
                test_data.getTestFunc(datas))  # 通过setattr自动为TestCase类添加成员方法，方法以“test_func_”开头
        # 动态添加测试用例
        suite.addTest(test_data("test_func_%s" % id))

    def test_suite(suite_datas, test_type, id='', case_name='', username='', project_id=0):
        suite = unittest.TestSuite()
        datas = eval(suite_datas)
        test = type(case_name, (Test,), {})
        T = test()
        T.start_test(datas, test, suite, id)
        now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        if test_type == 'case':
            path = UI_REPORT_PATH + "case/" + str(project_id) + "/"
            result_file = path + now + '_case_' + id + '_result.html'
        elif test_type == "task":
            path = UI_REPORT_PATH + "task/" + str(project_id) + "/"
            result_file = path + now + '_task_' + id + '_result.html'
        if not os.path.exists(os.path.join(os.getcwd(), path)):
            os.makedirs(os.path.join(os.getcwd(), path))

        runner = BeautifulReport(suite)
        result_list = runner.report(description=case_name, filename=result_file, log_path=".")
        date_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if test_type == "case":
            sql = """INSERT INTO ui_report(create_time, update_time, is_delete, ui_case_id, report_type, report_path,
                 file_name, username) VALUES ('%s', '%s', '%d', '%d', '%d', '%s', '%s', '%s')
                        """ % (
                date_time, date_time, 0, int(id), 1, result_file, os.path.split(result_file)[1], username)
            MySQLHelper().insert(sql)
        elif test_type == "task":
            sql = """INSERT INTO ui_report(create_time, update_time, is_delete, ui_task_id, report_type, report_path,
                             file_name, username) VALUES ('%s', '%s', '%d', '%d', '%d', '%s', '%s', '%s')
                            """ % (
                date_time, date_time, 0, int(id), 2, result_file, os.path.split(result_file)[1], username)
            MySQLHelper().insert(sql)

        return result_list
