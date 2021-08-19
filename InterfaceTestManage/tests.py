# # encoding=utf-8
# from django.test import TestCase
#
# # def test(*args,**kwargs):
# #     app = kwargs.pop('key1')
# #     print(app)
# #     print(kwargs)
# #     print(args)
# #
# # test('asdf',{'name':'zhangsan'},name ='java',key1=1212)
#
#
# '''
# 读取文件,对文件进行空格分隔，组装成字典
# '''
#
# # with open('C:\\Users\\Sam\Desktop\\test_11.txt','r',encoding='utf-8') as r:
# #     #print(r.read())
# #     #print(r.readline())
# #     #print(type(r.read()))
# #     #print(type(r.readlines()[0]))
# #     lists = r.readlines()
# #     dic ={}
# #     for i in lists:
# #         line = i.split()
# #         dic[line[0]]=line[1]
# #
# #     print(dic)
#
# with open('C:\\Users\\Sam\Desktop\\test_11.txt', 'w', encoding='utf-8') as r:
#     r.writelines(['keke', 'strong', 'finish'])
#
# # str = 'asdfasd'
# # str2 =''
# # for i in str:
# #     if(i=='d'):
# #         i='java'
# #     str2+=i
# # print(str2)
# str = '-asdfasd-'
# str = str.replace('d', 'java')
# print(str)
# print(str.count('a'))  # 没找到返回0,统计字符串出现的总数
# print(str.find('java'))  # 没找到返回-1，查找字符串，找到了就不会去找了
# str1 = str.join({'name': '张三', 'value': 18})
# print(str1)
# print("   ".isspace())

# suite_case_list = [{"id": 1, "suite_id": 1, "case_id": 1},
#                    {"id": 2, "suite_id": 1, "case_id": 2},
#                    {"id": 3, "suite_id": 2, "case_id": 3},
#                    {"id": 4, "suite_id": 2, "case_id": 4}]
# case_list = [{"id":1, "case_name": "11", "case_desc":"111", "project_id": 1},
#              {"id":2, "case_name": "22", "case_desc":"222", "project_id": 2},
#              {"id":3, "case_name": "33", "case_desc":"333", "project_id": 3},
#              {"id":4, "case_name": "44", "case_desc":"444", "project_id": 4}]
# project_list = [{'id': 1, 'project_name': '1项目'},
#                 {'id': 2, 'project_name': '2项目'},
#                 {'id': 3, 'project_name': '3项目'},
#                 {'id': 4, 'project_name': '4项目'}]

# for suite_case in suite_case_list:
#     for case in case_list:
#         if case["id"] == suite_case["case_id"]:
#             print(case["case_name"])
#             print(case["case_desc"])
#             for project in project_list:
#                 if project["id"] == case["project_id"]:
#                     print(project["project_name"])
# for i in range(10):
#     if 11 == i:
#         print(i)
# else:
#     print(123)
import time

import re

# print(re.findall(r'"name":"(.+?)"', '{"msg":"登录成功","code":0,"data":{"token":"ff3630b1-4932-4ebf-951a-14c23eb8db36","username":"超级管理员"}}'))

# print(re.findall("{{\w+}}\[\w+\]", '{"parentId": {{1asfaf}}[0], "page": "1", "limit": "10"}'))
import time
# start_time = time.time()
# time.sleep(11)
# print('{0:.3} s'.format((time.time() - start_time)))

import re

print(re.findall("{{\w+}}\[\w+\]",'{"organizationId": {{organization}}[0]}'))