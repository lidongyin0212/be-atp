from django.db import models

# Create your models here.


class BaseTable(models.Model):
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    is_delete = models.IntegerField(verbose_name='状态', default=0)  # 1 删除 0 有效

    class Meta:
        abstract = True
        verbose_name = '公有字段表'
        db_table = 'BaseTable'


'''UI用例'''
class Ui_Case(BaseTable):
    case_name = models.CharField('用例名称', null=True, max_length=256)
    case_desc = models.CharField('用例描述', null=True, max_length=600)
    username = models.CharField('操作人', max_length=20, null=False, default='')
    subsystem_id = models.IntegerField('子系统id', null=True)
    node_id = models.IntegerField('节点id', null=True)
    step_list = models.CharField('步骤列表', null=True, max_length=600)
    case_type = models.IntegerField('用例类型', null=True) # 1 普通用例；2 前置用例; 3 后置用例
    state = models.IntegerField('状态', default=0)  # 0 正常；1 停用

    class Meta:
        verbose_name = 'UI测试用例'
        db_table = 'ui_case'


'''UI用例步骤'''
class Ui_Case_Step(BaseTable):
    username = models.CharField('操作人', max_length=20, null=False, default='')
    case_id = models.IntegerField('用例ID', null=True)
    step_element_id = models.IntegerField('步骤元素id', null=True)
    step_action = models.CharField('元素操作', null=True, max_length=50)
    step_params = models.CharField('操作参数', null=True, max_length=600)
    extract_param = models.CharField('提取变量', null=True, max_length=50)
    state = models.IntegerField('状态', default=0)  # 0 正常；1 停用

    class Meta:
        verbose_name = 'UI测试步骤'
        db_table = 'ui_case_step'


'''UI元素管理'''
class Ui_Element(BaseTable):
    element_name = models.CharField('元素名称', null=True, max_length=256)
    username = models.CharField('操作人', max_length=20, null=False, default='')
    case_id = models.IntegerField('用例ID', null=True)
    element_located_method = models.CharField('元素定位方法', null=True, max_length=50)
    element_location = models.CharField('元素定位', null=True, max_length=600)
    state = models.IntegerField('状态', default=0)  # 0 正常；1 停用

    class Meta:
        verbose_name = 'UI元素管理'
        db_table = 'ui_element'


'''UI节点管理'''
class Ui_Node(BaseTable):
    node_name = models.CharField('节点名称', null=True, max_length=256)
    node_ip = models.CharField('节点IP', null=True, max_length=16)
    node_port = models.CharField('节点端口', null=True, max_length=8)
    browser = models.CharField('浏览器类型', null=True, max_length=16)
    username = models.CharField('操作人', max_length=20, null=False, default='')
    pid = models.CharField('pid', max_length=20, null=False, default='')
    state = models.IntegerField('状态', default=0)  # 0 正常；1 停用

    class Meta:
        verbose_name = 'UI节点'
        db_table = 'ui_node'


"""UI任务管理"""
class Ui_Task(BaseTable):
    task_name = models.CharField('任务名称', null=True, max_length=256)
    task_desc = models.CharField('任务描述', null=True, max_length=600, default="")
    project_id = models.IntegerField('项目id', null=True)
    node_id = models.IntegerField('节点id', null=True)
    step_list = models.TextField('步骤列表', null=True, max_length=600, default='')
    execute_result = models.CharField('执行结果', max_length=20, null=True, default="")
    cron = models.CharField('cron', max_length=300, null=True, default="")
    state = models.IntegerField('状态', default=0)  # 0 未启动；1 运行中
    username = models.CharField('操作人', max_length=20, null=False, default="")

    class Meta:
        verbose_name = 'UI任务'
        db_table = 'ui_task'


"""UI任务报告"""
class Ui_Report(BaseTable):
    task_id = models.IntegerField('任务id', null=True)
    report_path = models.CharField(
        '报告路径', null=True, max_length=256, default="")
    file_name = models.CharField('报告名称', null=True, max_length=256, default="")
    username = models.CharField('操作人', max_length=20, null=False, default="")
    report_type = models.IntegerField('类型', null=True)  # 0=普通  1=任务
    job_status = models.IntegerField('执行状态', null=True)  # 0 测试执行完成，1测试执行中

    class Meta:
        verbose_name = '任务和报告关系表'
        db_table = 'ui_report'