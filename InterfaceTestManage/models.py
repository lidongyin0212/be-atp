# coding=utf-8

from django.db import models


# Create your models here.
class BaseTable(models.Model):
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    is_delete = models.IntegerField(verbose_name='状态', default=0, null=True)  # 1 删除 0 有效

    class Meta:
        abstract = True
        verbose_name = '公有字段表'
        db_table = 'BaseTable'


class Sys_req_cookie(models.Model):
    username = models.CharField(help_text='用户名', max_length=20, null=False, default="")
    cookie_param = models.CharField(
        help_text='cookie参数', null=False, default="", max_length=3000)
    project_id = models.IntegerField(help_text='项目id', null=True)
    headers = models.TextField('header_auth', null=True, default='')
    task_id = models.IntegerField('任务id', null=True)
    global_variable = models.TextField('全局变量', null=True, default='')

    class Meta:
        unique_together = ('username', 'project_id', 'task_id')
        verbose_name = 'cookie表'
        db_table = 'sys_req_cookie'


'''用户'''


class Sys_user_info(BaseTable):
    username = models.CharField('用户名', max_length=20, null=False, default="")
    username_cn = models.CharField('用户名中文', max_length=20, null=False, default="")
    email = models.EmailField('邮箱', max_length=128, null=True)
    role = models.IntegerField('用户角色', null=True)
    password = models.CharField('密码', max_length=20, null=False, default="")
    state = models.IntegerField('状态', default="0") #0:未激活  1:激活
    operator = models.CharField('操作人', max_length=20, null=False, default='')

    class Meta:
        verbose_name = '用户信息表'
        db_table = 'sys_user_info'


'''用户项目权限'''


class Sys_user_permission(BaseTable):
    user_id = models.IntegerField('用户id', null=True)
    project_id = models.IntegerField('项目id', null=True)
    username = models.CharField('操作人', max_length=20, null=False, default='')

    class Meta:
        verbose_name = '用户权限表'
        db_table = 'sys_user_permission'


'''项目管理'''


class Sys_project(BaseTable):
    project_name = models.CharField('项目名称', max_length=128, default="")
    project_desc = models.TextField('项目说明', null=True, default="")
    username = models.CharField('操作人', max_length=20, null=False, default='')

    class Meta:
        verbose_name = '项目表'
        db_table = 'sys_project'


'''系统'''


class Sys_subsystem(BaseTable):
    subsystem_name = models.CharField('系统名称', max_length=128, default="")
    subsystem_desc = models.TextField('系统说明', null=True, default="")
    username = models.CharField('操作人', max_length=20, null=False, default='')
    project_id = models.IntegerField('项目id', null=True)

    class Meta:
        verbose_name = '系统表'
        db_table = 'sys_subsystem'


'''模块'''


class Sys_module(BaseTable):
    type_choices = (('正常用例模块', 1), ('前置条件模块', 2), ('后置条件模块', 3))
    module_name = models.CharField('模块名称', max_length=128, default="")
    module_desc = models.TextField('模块说明', null=True, default="")
    module_type = models.IntegerField('模块类型', choices=type_choices, default=1)
    parent_id = models.IntegerField('上级id', null=True)
    subsystem_id = models.IntegerField('子系统id', null=True)
    env_id = models.IntegerField('环境id', null=True)
    case_list = models.TextField('用例列表', null=True, default="")
    sub_module_list = models.TextField('子模块列表', null=True, default="")
    report_path = models.TextField('报告路径', null=True, default="")
    username = models.CharField('操作人', max_length=20, null=False, default='')
    operater = models.CharField('执行人', max_length=20, null=False, default='')
    project_id = models.IntegerField(help_text='项目id', null=True)

    class Meta:
        verbose_name = '模块表'
        db_table = 'sys_module'


'''环境管理'''


class Sys_env(BaseTable):
    env_name = models.CharField('环境名称', null=True, max_length=128, default="")
    env_desc = models.TextField('环境简介', null=True, default="")
    host = models.CharField('主机名称', null=True, max_length=128, default="")
    port = models.CharField('端口号', null=False, max_length=8, default="")
    project_id = models.IntegerField('项目id', null=True)
    state = models.IntegerField('启用状态码', default=1)  # 1 启用 2不启用
    username = models.CharField('操作人', max_length=20, null=False, default="")
    subsystem_id = models.IntegerField('子系统id', null=True)
    creator = models.CharField('创建人', max_length=20, null=False, default="")

    class Meta:
        verbose_name = '环境配置表'
        db_table = 'sys_env'


'''接口'''


class Inte_interface(BaseTable):
    interface_name = models.CharField('接口名称', null=False, max_length=256, default="")
    req_path = models.CharField('请求路径', null=False, max_length=200, default="")
    req_method = models.CharField('请求方式', null=True, max_length=20, default="")
    req_headers = models.TextField('请求头', null=True, default="")
    req_param = models.TextField('请求参数', null=True, default="")
    req_body = models.TextField('请求体参数', null=True, default="")
    req_file = models.TextField('请求文件', null=True, default="")
    extract_list = models.CharField('提取规则', null=True, max_length=3000, default='')
    except_list = models.CharField('期望结果', null=True, max_length=3000, default='')
    state = models.IntegerField('接口状态', null=True, default=1)
    excute_result = models.TextField('执行结果', null=True, default="")
    subsystem_id = models.IntegerField('子系统id', null=True)
    env_id = models.IntegerField('环境id', null=True)
    username = models.CharField('操作人', max_length=20, null=False, default="")
    creator = models.CharField('创建人', max_length=20, null=False, default="")
    project_id = models.IntegerField(help_text='项目id', null=True)

    class Meta:
        verbose_name = '接口表'
        db_table = 'inte_interface'


'''用例表'''


class Inte_case(BaseTable):
    type_choices = (('正常用例', 1), ('前置条件用例', 2), ('后置条件用例', 3))
    case_name = models.CharField('用例名称', null=True, max_length=256, default="")
    req_path = models.CharField('请求路径', null=False, max_length=200, default="")
    req_method = models.CharField('请求方式', null=False, max_length=20, default="")
    req_headers = models.TextField('请求头', null=True, default="")
    req_param = models.TextField('请求参数', null=True, default="")
    req_body = models.TextField('请求体参数', null=True, default="")
    req_file = models.TextField('请求文件', null=True, default="")
    extract_list = models.CharField('提取规则', null=True, max_length=3000, default='')
    except_list = models.CharField('期望结果', null=True, max_length=3000, default='')
    is_mock = models.BooleanField('mock开启状态', null=True, default=False)
    mock_id = models.IntegerField('mock id', null=True)
    run_time = models.IntegerField('执行次数', null=True, default=1)
    wait_time = models.IntegerField('等待时间', null=True, default=0)
    state = models.IntegerField('接口状态', null=True, default=1)
    excute_result = models.TextField('执行结果', null=True, default="")
    interface_id = models.IntegerField('接口id', null=True)
    module_id = models.IntegerField('module id', null=True)
    username = models.CharField('操作人', max_length=20, null=False, default="")
    case_type = models.IntegerField('用例类型', choices=type_choices, default=1)
    creator = models.CharField('创建人', max_length=20, null=False, default="")

    class Meta:
        verbose_name = '用例表'
        db_table = 'inte_case'


'''任务'''


class Inte_task(BaseTable):
    task_name = models.CharField('任务名称', null=True, max_length=256, default="")
    task_desc = models.CharField('任务描述', null=True, max_length=600, default="")
    case_list = models.TextField('用例列表', null=True, default='')
    case_dict = models.TextField('子系统用例字典', null=True, default='')
    execute_result = models.CharField('执行结果', max_length=20, null=True, default="")
    cron = models.CharField('cron', max_length=300, null=True, default="")
    project_id = models.IntegerField('项目id', null=True)
    state = models.IntegerField('状态', default=0)  # 0 未启动；1 运行中
    job_id = models.IntegerField('xxl-job-id', null=True)
    username = models.CharField('操作人', max_length=20, null=False, default="")
    excel_file_name = models.CharField('报告导出结果', max_length=100, null=False, default="")
    creator = models.CharField('创建人', max_length=20, null=False, default="")

    class Meta:
        verbose_name = '任务'
        db_table = 'inte_task'


'''任务与接口的关系表'''


class Inte_task_case(BaseTable):
    task_id = models.IntegerField('任务id', null=True)
    case_id = models.IntegerField('用例id', null=True)
    case_name = models.CharField('用例名称', null=True, max_length=256, default="")
    req_path = models.CharField('请求路径', null=False, max_length=200, default="")
    req_method = models.CharField('请求方式', null=False, max_length=20, default="")
    req_headers = models.TextField('请求头', null=True, default="")
    req_param = models.TextField('请求参数', null=True, default="")
    req_body = models.TextField('请求体参数', null=True, default="")
    req_file = models.TextField('请求文件', null=True, default="")
    extract_list = models.CharField('提取规则', null=True, max_length=3000, default='')
    except_list = models.CharField('期望结果', null=True, max_length=3000, default='')
    is_mock = models.BooleanField('mock开启状态', null=True, default=False)
    mock_id = models.IntegerField('mock id', null=True)
    run_time = models.IntegerField('执行次数', null=True, default=1)
    wait_time = models.IntegerField('等待时间', null=True, default=0)
    state = models.IntegerField('接口状态', null=True, default=1)
    excute_result = models.TextField('执行结果', null=True, default="")
    env_id = models.IntegerField('环境id', null=True)
    username = models.CharField('操作人', max_length=20, null=False, default="")
    creator = models.CharField('创建人', max_length=20, null=False, default="")

    class Meta:
        verbose_name = '任务和接口关系表'
        db_table = 'inte_task_case'


class Inte_task_record(BaseTable):
    task_id = models.IntegerField('任务id')
    execute_count = models.IntegerField('执行次数', null=True, default=0)
    success_count = models.IntegerField('成功次数', null=True, default=0)
    fail_count = models.IntegerField('失败次数', null=True, default=0)
    assert_count = models.IntegerField('断言失败次数', null=True, default=0)

    class Meta:
        verbose_name = '任务执行记录表'
        db_table = 'inte_task_record'


'''报告记录表'''


class Inte_report(BaseTable):
    task_id = models.IntegerField('任务id', null=True)
    report_path = models.CharField(
        '报告路径', null=True, max_length=256, default="")
    file_name = models.CharField('报告名称', null=True, max_length=256, default="")
    username = models.CharField('操作人', max_length=20, null=False, default="")
    report_type = models.IntegerField('类型', null=True)  # 0=普通  1=任务
    job_status = models.IntegerField('执行状态', null=True)  # 0 测试执行完成，1测试执行中
    job_count = models.TextField('用例数', null=True, default='')

    # type = models.IntegerField('类型', null=True)  # 0=普通  1=任务
    # status = models.IntegerField('执行状态', null=True)  # 0 测试执行完成，1测试执行中
    # count = models.TextField('用例数', null=True, default='')
    class Meta:
        verbose_name = '测试集和用例关系表'
        db_table = 'inte_report'


'''数据库依赖环境'''


class Sys_db_env(BaseTable):
    type_choices = (('redis', 1), ('mysql', 2), ('mongodb', 3))
    project_id = models.IntegerField('项目id', null=True)
    db_type = models.IntegerField('数据库类型', choices=type_choices, default=1)
    env_desc = models.CharField('环境描述', max_length=256, null=True, default="")
    env_name = models.CharField('环境名称', max_length=128, null=True, default="")
    env_ip = models.CharField('ip地址', max_length=20, null=True, default="")
    env_port = models.CharField('端口', max_length=20, null=True, default="")
    user = models.CharField('用户名', max_length=128, null=True, default="")
    password = models.CharField('密码', max_length=30, null=True, default="")
    dbname = models.CharField('数据库名', max_length=128, null=True, default="")
    username = models.CharField('操作人', max_length=20, null=True, default="")
    creator = models.CharField('创建人', max_length=20, null=False, default="")

    class Meta:
        verbose_name = '数据库环境'
        db_table = 'sys_db_env'


# sql语句详情
class Sys_db_sqldetail(BaseTable):
    type_choices = (('禁用', 0), ('激活', 1))
    env_id = models.IntegerField('数据库环境id', null=True)
    sql_name = models.CharField('sql名称', max_length=128, null=True, default="")
    sql = models.CharField('sql', max_length=4000, null=True, default="")
    state = models.IntegerField('状态', choices=type_choices, default=1)
    result = models.CharField('结果', max_length=2000, null=True, default="")
    username = models.CharField('操作人', max_length=20, null=True, default="")
    remark = models.CharField('备注', max_length=255, null=False, default="")

    class Meta:
        index_together = ('sql_name', 'env_id')
        verbose_name = '查询语句'
        db_table = 'sys_db_sqldetail'


class Sys_mock_server(BaseTable):
    type_choices = (('禁用', 0), ('激活', 1))
    mock_name = models.CharField('mock名称', max_length=128, null=False, default="")
    mock_router = models.CharField(
        'mock路由', max_length=50, null=False, default="")
    mock_path = models.CharField(
        'mock路径', max_length=200, null=False, default="")
    mock_json = models.TextField('响应json', default="")
    mock_state = models.IntegerField('mock状态', choices=type_choices, default=0)
    username = models.CharField('操作人', max_length=20, null=True, default="")

    class Meta:
        verbose_name = 'mock服务'
        db_table = 'sys_mock_server'


# 公用参数
class Sys_public_param(BaseTable):
    state_choices = (('禁用', 0), ('激活', 1))
    type_choices = (('提取变量', 1), ('自定义变量', 2), ('数据库变量', 3))
    param_name = models.CharField('变量名称', max_length=128, null=False, default="")
    param_desc = models.CharField('变量描述', max_length=256, null=True, default="")
    rule = models.CharField('变量规则', max_length=256, null=True, default="")
    input_params = models.CharField('函数入参', max_length=500, null=True, default="")
    state = models.IntegerField('状态', choices=state_choices, default=1)
    param_type = models.IntegerField('类型', choices=type_choices, default=1)
    data_format = models.CharField('服务器返回的数据格式', null=True, max_length=50, default='')
    username = models.CharField('操作人', max_length=20, null=True, default="")
    project_id = models.IntegerField('项目id', null=True)
    creator = models.CharField('创建人', max_length=20, null=False, default="")

    class Meta:
        index_together = ('param_name', 'project_id')
        verbose_name = '共用变量'
        db_table = 'sys_public_param'


# 提取依赖数据变量
class Inte_extract(BaseTable):
    param_name = models.CharField('变量名称', max_length=128, null=False, default="")
    param_desc = models.CharField('变量描述', max_length=256, null=True, default="")
    rule = models.CharField('变量规则', max_length=256, null=True, default="")
    data_format = models.CharField('服务器返回的数据格式', null=True, max_length=50, default='')
    project_id = models.IntegerField('项目id', null=True)
    subsystem_id = models.IntegerField('系统id', null=True)
    username = models.CharField('操作人', max_length=20, null=True, default="")

    class Meta:
        index_together = ('param_name', 'project_id') # 普通索引
        verbose_name = '提取变量'
        db_table = 'inte_extract'


# 系统字典
class Sys_dict(models.Model):
    dict_key = models.CharField('字典key', max_length=50, null=False, default="")
    dict_value = models.CharField('字典值', max_length=50, null=False, default="")
    dict_type = models.IntegerField('类型', null=True)  # 1是自定义变量类型， 2是行为，3是操作对象名称
    if_param = models.IntegerField('函数参数', null=True) #是否需要函数参数  0是不需要传函数参数  1是需要

    class Meta:
        verbose_name = '字典'
        db_table = 'sys_dict'


'''加密'''


class Sys_encryption(BaseTable):
    variable_name = models.CharField('变量名称', max_length=40, null=False, default="")
    request_method = models.CharField('请求方法', max_length=20, null=False, default="")
    url = models.CharField('URL', max_length=256, null=False, default="")
    publickey = models.TextField('公钥', max_length=1024, null=False, default="")
    plaintext = models.CharField('明文', max_length=255, null=False, default="")
    extract_field = models.CharField('提取字段', max_length=255, null=False, default="")
    encr_type = models.IntegerField('加密类型', null=False, default=0)
    username = models.CharField('操作人', max_length=20, null=False, default='')
    remark = models.CharField('备注', max_length=255, null=False, default="")
    project_id = models.IntegerField('项目id', null=True)

    class Meta:
        verbose_name = '加密表'
        db_table = 'sys_encryption'


'''数据驱动'''


class Sys_data_driven(BaseTable):
    param_name = models.CharField('参数名称', max_length=128, default="")
    param_list = models.TextField('参数列表', default="")
    remark = models.TextField('备注', default="")
    project_id = models.IntegerField('项目id', null=True)
    username = models.CharField('操作人', max_length=20, null=True, default="")
    creator = models.CharField('创建人', max_length=20, null=False, default="")

    class Meta:
        verbose_name = '数据驱动'
        db_table = 'sys_data_driven'


'''用户操作记录'''


class Sys_user_operate(models.Model):
    operate_time = models.DateTimeField(verbose_name='运行时间', auto_now_add=True)
    username = models.CharField('操作人', max_length=20, null=True, default="")
    behavior = models.CharField('行为', max_length=128, null=True, default="")
    object_name = models.CharField('对象名称', max_length=20, null=True, default="")
    object_desc = models.CharField('对象说明', max_length=1024, null=True, default="")

    class Meta:
        verbose_name = '用户操作记录'
        db_table = 'sys_user_operate'
