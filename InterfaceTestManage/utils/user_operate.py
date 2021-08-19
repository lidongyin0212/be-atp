# -*- coding:utf-8 -*-
from InterfaceTestManage.models import Sys_user_operate
import time


def user_operate(username, behavior, object_name, object_desc):
    '''
    :param operate_time: 运行时间
    :param username: 操作人
    :param behavior: 行为
    :param object_name: 对象名称
    :param object_desc: 对象描述
    :return:
    '''
    operate_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    Sys_user_operate.objects.create(
        operate_time=operate_time,
        username=username,
        behavior=behavior,
        object_name=object_name,
        object_desc=object_desc
    )
