# -*- coding: utf-8 -*-
import requests
import json
from public.publicfun import *
from public.mysqldb import MySQLHelper
# 往xxl-job 添加任务
def add_scheduler(task_name, username, password, cron,task_id, alarmEmail):
    url = "%s/xxl-job-admin/api/jobinfo/add" % get_url() # xxl-job服务
    run_url = get_run_url()  #xxl-job 运行对象的url
    password=password
    data = {
        "jobGroup": 4,
        "jobDesc": task_name,
        "author": username,
        "alarmEmail": alarmEmail,
        "scheduleType": "CRON",
        "scheduleConf": cron,
        "cronGen_display": cron,
        "schedule_conf_CRON": cron,
        "schedule_conf_FIX_RATE": "",
        "schedule_conf_FIX_DELAY": "",
        "glueType": "GLUE_GROOVY", # java 执行模式
        "executorHandler": "",
        "executorParam": "",
        "executorRouteStrategy": "FIRST",
        "childJobId": "",
        "misfireStrategy": "DO_NOTHING",
        "executorBlockStrategy": "SERIAL_EXECUTION",
        "executorTimeout": 0,
        "executorFailRetryCount": 0,
        "glueRemark": "GLUE代码初始化",
        "glueSource":'%s/api/login@%s@%s@%s/api/execute_tasks/%s' %
                     (run_url,"xxl-job","123456",run_url,task_id)
        # "glueSource": 'requests.session().post(url="%s/api/execute_tasks/%s",'
        #       'data=json.dumps({"source":"once"}),'
        #       'cookies=requests.utils.dict_from_cookiejar(requests.post(url="%s/api/login",'
        #       'data=json.dumps({"username":"%s","password":"%s"})).cookies)).text.encode("utf-8").decode("unicode_escape")' % (
        #     run_url, task_id, run_url, username, password)

    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    result = json.loads(requests.session().post(url=url, data=data, headers=headers).text)
    return result["content"], result

# 编辑任务
def edit_scheduler(id, cron, task_name, username):
    url = "%s/xxl-job-admin/api/jobinfo/update" % get_url()
    # cron = cron[0:10] + '?'
    data = {
            "jobGroup": 4,
            "jobDesc":task_name,
            "author":username,
            "alarmEmail":"",
            "scheduleType":"CRON",
            "scheduleConf":cron,
            "cronGen_display":cron,
            "schedule_conf_CRON":cron,
            "schedule_conf_FIX_RATE":"",
            "schedule_conf_FIX_DELAY":"",
            "executorHandler":"",
            "executorParam":"",
            "executorRouteStrategy":"FIRST",
            "childJobId":"",
            "misfireStrategy":"DO_NOTHING",
            "executorBlockStrategy":"SERIAL_EXECUTION",
            "executorTimeout":0,
            "executorFailRetryCount": 0,
            "id":int(id)
            }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    result = json.loads(requests.session().post(url=url, data=data, headers=headers).text)
    return result

# 删除任务
def del_scheduler(id):
    url = "%s/xxl-job-admin/api/jobinfo/remove" % get_url()
    data = {"id":int(id)}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    result = json.loads(requests.session().post(url=url, data=data, headers=headers).text)
    return result

# 启动任务
def start_scheduler(id):
    url = "%s/xxl-job-admin/api/jobinfo/start" % get_url()
    data = {"id":int(id)}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    result = json.loads(requests.session().post(url=url, data=data, headers=headers).text)
    return result

#停止任务
def stop_scheduler(id):
    xxl_url = "%s/xxl-job-admin/api/jobinfo/stop" % get_url()
    data = {"id":int(id)}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    result = json.loads(requests.session().post(url=xxl_url, data=data, headers=headers).text)
    return result

def get_url():
    # xxl-job 服务的url dict_type=4
    url = MySQLHelper().get_one("""select dict_value from `sys_dict` where dict_type=4""")
    if type(url) == tuple:
        run_url = ''.join(url)
        return run_url
    return url

def get_run_url():
    url =  MySQLHelper().get_one("""select dict_value from `sys_dict` where dict_type=5""")
    if type(url) == tuple:
        run_url = ''.join(url)
        return run_url
    return url
if __name__ == '__main__':
    pass
    # get_url()
#     task_name = "任务一"
#     username = "admin"
#     cron = "0 0 * * * ?"
#     password = "123456"
#     task_id = 25
    # add_scheduler(task_name,username,password,cron,task_id)
    # print(start_scheduler(20))
    # stop_scheduler(20)
    # del_scheduler(11)
    # edit_scheduler(18, cron, task_name, username)

