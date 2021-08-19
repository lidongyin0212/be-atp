UI_REPORT_PATH = "result/test_result/ui/"
INTERFACE_REPORT_PATH = 'result/test_result/interface/'
APP_REPORT_PATH = 'result/test_result/app/'

REPORT_PATH = "result/screen_shot/ui/"

PROJECT_ADD_CONTEXT = {'title': '增加项目', 'btn': '增加'}
PROJECT_NOT_FOUND = "项目不存在"
SUBSYSTEM_NOT_FOUND = "子系统不存在"
VERSION_NOT_FOUND = "版本不存在"
MODULE_NOT_FOUND = "模块不存在"
ENV_NOT_FOUND = "环境不存在"
PARENT_MODULE_NOT_FOUND = "父级模块不存在"
TASK_NOT_FOUND = "任务不存在"
TASK_IS_EMPTY = "任务用例为空"
# PARAM_TYPE_DICT = {"1": "提取变量", "2": "自定义变量", "3": "数据库变量"}

INTERFACE_NAME_EXIST = "接口名称已存在"
INTERFACE_PATH_EXIST = "请求路径已存在"
NAME_REPETITION = "名称已存在"
EXTRACT_NAME_REPRTITION = "引用名称已存在"
CASE_NAME_EXIST = "用例名称已存在"

INTERFACE_INFO_200 = "<b>接口</b>：%s,请求成功"
INTERFACE_INFO_500 = "<b>接口</b>:%s,请求失败，<br> %s"

ADD_SUCCESS_200 = "添加成功"
ADD_FAIL_500 = "添加失败"
EDIT_SUCCESS_200 = "修改成功"
EDIT_FAIL_500 = "修改失败"
DEL_SUCCESSS_200 = "删除成功"
DEL_FAIL_500 = "删除失败"
MOVE_SUCCESS_200 = "移动成功"
MOVE_FAIL_500 = "移动失败"

PERMISSION_SUCCESSS_200 = "授权成功"
PERMISSION_FAIL_500 = "授权失败"
NOT_PERMISSION = "无权限"

CASE_INFO_200 = "用例执行成功"

ACTIVE_SUCCESS_200 = "激活成功"
ACTIVE_FAIL_500 = "激活失败"

SERVER_ERROR = "服务器错误"
USE_MSG = "%s关联了%s"
USING_MSG = "%s正在使用"

DATABASE_CONNECT_SUCCESSS = "数据库连接成功"
DATABASE_CONNECT_FAIL = "数据库连接失败"

DATA_NOT_FOUND = "找不到数据"

RUN_TASK_SUCCESS_200 = "开始执行任务"
RUN_TASK_FAIL_500 = "任务执行失败"
TASKING = "删除失败，请检查任务是否在运行中或者关联了用例"

STOP_TASK_SUCCESS_200 = "任务停止成功"
STOP_TASK_FAIL_500 = "任务停止失败"

SQL_OPERATE_SUCCESS_200 = "%s成功"
SQL_OPERATE_FAIL_500 = "%s失败, %s"

DATA_NO_FOUND = "%s未找到"
USERINFO_NOT_FIND = "用户信息不存在"

EXECUTE_CASE_SUCCESS = "用例执行成功！"
EXECUTE_CASE_FAIL = "用例执行失败,尽快查看日志看看错误信息！"
EXECUTE_CASE_EXCEPT = "请检测请求地址是否正确,执行发送请求出现异常了！异常信息是:%s"

NOT_METHMOD = "无该请求方式"
NOT_TYPE = "无该类型"
NOT_LIST = "参数类型不是list"
NOT_PARAM = "缺失参数"

NOT_ID = "ID不存在"
NOT_WRITE_NAME = "请填写名称"
NAME_INPUT_LONG = "名称输入超长"
DESC_INPUT_LONG = "说明输入超长"

NOT_CHOOSE_SELF = "不能选择自身模块作为上级模块"

NOT_PARAM_NAME = "该参数未保存"
PARAM_NAME_GENERATOR_SUCCESS = "参数生成成功"
PARAM_NAME_GENERATOR_FAIL = "参数生成失败"

SUBSYSTEM_NOT_CASE = "该系统下用例为空"
MODULE_NOT_CASE = "该模块下用例为空"
SUBSYSTEM_NOT_ENV = "系统下模块未绑定环境"
MODULE_NOT_ENV = "模块未绑定环境"
CASE_NOT_ENV = "用例未找到"

IMPORT_PARAMS_NOT_URL = "缺失Swagger URL"
IMPORT_PARAMS_NOT_JSON = "缺失Swagger JSON数据"
IMPORT_SWAGGER_DATA_ERR = "导入失败,请确认URL或文件是否正确"

INPUT_LONG = "输入超长"