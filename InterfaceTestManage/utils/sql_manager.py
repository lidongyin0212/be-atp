# TODO 首页数据
PROJECT_DATA = """select count(sys_project.id),sum(interface_count),sum(case_count),sum(task_count),
                sum(tasking_count) from sys_project 
                left join (select count(interface_name) interface_count, project_id from inte_interface left join 
                sys_project on sys_project.id=inte_interface.project_id
                where inte_interface.is_delete=0 and inte_interface.state=1 group by project_id) api
                on sys_project.id = api.project_id 						
                left join (select count(case_name) case_count,project_id from inte_case 
                left join inte_interface on inte_interface.id = inte_case.interface_id
                where inte_case.is_delete=0 
                and inte_case.state=1 and case_type=1 group by project_id) ca on sys_project.id = ca.project_id
                left join (select project_id, count(task_name) task_count, sum(case when state=1 then 1 else 0 end) tasking_count
                from inte_task where inte_task.is_delete=0 group by project_id) tsk on sys_project.id = tsk.project_id 
                left join sys_user_permission on sys_user_permission.project_id=sys_project.id
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                where sys_user_info.username='%s' and sys_user_permission.is_delete=0 and sys_user_info.is_delete=0
                and sys_project.is_delete=0 """

BAR_DATA_PROJECT = """select sys_project.id,project_name,ifnull(interface_count,0),ifnull(case_count,0) from sys_project 
              left join (select count(interface_name) interface_count, project_id from inte_interface left join 
              sys_project on sys_project.id=inte_interface.project_id
              where inte_interface.is_delete=0 and inte_interface.state=1 group by project_id) api on sys_project.id = api.project_id 
              left join (select count(case_name) case_count,project_id from inte_case 
              left join inte_interface on inte_interface.id = inte_case.interface_id
              where inte_case.is_delete=0 and 
              inte_case.state=1 and case_type=1 group by project_id) ca on sys_project.id = ca.project_id
              left join sys_user_permission on sys_user_permission.project_id=sys_project.id
              left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
              where sys_user_info.username='%s' and sys_user_permission.is_delete=0 and sys_user_info.is_delete=0 
              and sys_project.is_delete=0
              """

BAR_DATA_SUBSYSTEM = """select sys_project.id,project_name,ifnull(interface_count,0),ifnull(case_count,0) from sys_project 
              left join (select count(interface_name) interface_count, project_id from inte_interface left join 
              sys_project on sys_project.id=inte_interface.project_id
              where inte_interface.is_delete=0 and inte_interface.state=1 group by project_id) api on sys_project.id = api.project_id 
              left join (select count(case_name) case_count,project_id from inte_case 
              left join inte_interface on inte_interface.id = inte_case.interface_id
              where inte_case.is_delete=0 and 
              inte_case.state=1 and case_type=1 group by project_id) ca on sys_project.id = ca.project_id
              left join sys_user_permission on sys_user_permission.project_id=sys_project.id
              left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
              where sys_user_info.username='%s' and sys_user_permission.is_delete=0 and sys_user_info.is_delete=0 
              and sys_project.is_delete=0 and sys_project.id=%s
              """

LINE_DATA = """select a.click_date, ifnull(b.count,0), ifnull(b.success_count,0), ifnull(b.assert_count,0), 
            ifnull(b.fail_count,0)
            from (
                    SELECT
                        @cdate := DATE_ADD( @cdate, INTERVAL - 1 DAY ) click_date
                    FROM
                        ( SELECT @cdate := DATE_ADD( CURDATE( ), INTERVAL + 1 DAY ) FROM inte_task_record ) t1 
                    WHERE
                        @cdate > DATE_SUB(CURDATE(),INTERVAL %s DAY ) 
            ) a left join (
                select date(inte_task_record.create_time) as datetime, sum(execute_count) 
                count,sum(success_count) success_count,
                sum(fail_count) fail_count, sum(assert_count) assert_count from inte_task_record 
                left join inte_task on inte_task.id = inte_task_record.task_id
                left join sys_project on sys_project.id = inte_task.project_id
                left join sys_user_permission on sys_user_permission.project_id = sys_project.id
                left join sys_user_info on sys_user_info.id = sys_user_permission.user_id
                where sys_user_info.username=%s and sys_user_permission.is_delete=0 
                and (case when not %s then 1 else inte_task.project_id=%s end)
                group by date(create_time)
            ) b on a.click_date = b.datetime order by a.click_date"""

# TODO 权限模块
#  0全部 1 离线 2 在线
# PERMISSION_LIST_LIKE = """select id, username, username_cn, role, email,
#                 DATE_FORMAT(create_time, '%%Y-%%m-%%d %%H:%%i:%%S'),DATE_FORMAT(update_time, '%%Y-%%m-%%d %%H:%%i:%%S'),
#                 operator from sys_user_info where is_delete=0 and state=1 and CONCAT(username,  username_cn) like '%%%s%%'"""

PERMISSION_LIST_LIKE = """select id, username, username_cn, role, email,
                DATE_FORMAT(create_time, '%%Y-%%m-%%d %%H:%%i:%%S'),DATE_FORMAT(update_time, '%%Y-%%m-%%d %%H:%%i:%%S'),
                operator, case when update_time between date_add(now(), interval - 5 minute) and now() then '在线' else '离线' end
                 from sys_user_info where is_delete=0 and state=1 and CONCAT(username,  username_cn) like '%%%s%%' and
                case when %s=2 then update_time between date_add(now(), interval - 5 minute) and now()
                when %s=1 then update_time < date_add(now(), interval - 5 minute)
                else 1 end
                """

CHECK_PERMISSION_LIST_LIKE = """select id, username,username_cn, role, email, 
                DATE_FORMAT(create_time, '%%Y-%%m-%%d %%H:%%i:%%S'),DATE_FORMAT(update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), 
                operator, '' from sys_user_info where is_delete=0 and state=0 and CONCAT(username,  username_cn) like '%%%s%%'"""

USER_PERMISSION_TREE = """select sys_user_info.id, sys_project.id, sys_user_info.username_cn,case when 
                sys_user_permission.is_delete=0 then project_name else '' end , role, sys_user_info.username
                from sys_user_info left join sys_user_permission on sys_user_info.id=user_id
                left join sys_project on sys_project.id=project_id where sys_user_info.is_delete=0 and state=1 
                and CONCAT(sys_user_info.username,  sys_user_info.username_cn) like '%%%s%%'"""

PROJECT_PERMISSION_TREE = """select sys_project.id, user_id, project_name, case when sys_user_permission.is_delete='0' then 
                sys_user_info.username_cn else '' end
                from sys_project left join sys_user_permission on sys_project.id=project_id 
                left join sys_user_info on user_id=sys_user_info.id where sys_project.is_delete=0 
                and CONCAT(sys_project.project_name) like '%%%s%%'"""
# TODO# 项目模块

# 项目模糊查询
# PROJECT_LIST_LIKE = """select sys_project.id, project_name, project_desc,
#                 case when interface_count then interface_count else 0 end,
#                 case when case_count then case_count else 0 end,
#                 case when inte_case_count then inte_case_count else 0 end,
#                 DATE_FORMAT(sys_project.create_time, '%%Y-%%m-%%d %%H:%%i:%%S')
#                 from sys_project left join  ((
#                 select project_id, count(interface_name) interface_count
#                 from inte_interface where is_delete=0 and state=1 group by project_id) a
#                 left join
#                 (select project_id, count(case_name) case_count
#                 from `case` where is_delete=0 and type='' group by project_id) b
#                 on a.project_id=b.project_id
#                 left join (select `case`.project_id ,count(interface_name) inte_case_count
#                 from inte_case left join `case` on `case`.id=inte_case.case_id where
#                 inte_case.is_delete=0 and `case`.is_delete=0 and type='' and inte_case.state=1 group by `case`.project_id) c
#                 on a.project_id=c.project_id)
#                 on sys_project.id=a.project_id
#                 left join sys_user_permission on sys_user_permission.project_id=sys_project.id
#                 left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
#                 where sys_user_info.username='%s' and sys_user_permission.is_delete=0
#                 and sys_user_info.is_delete=0 and project_name like '%%%s%%' order by sys_project.create_time desc"""

'''项目权限校验'''
PROJECT_PERMISSION_CHEKE = """select sys_project.id from sys_user_permission
                    left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                    left join sys_project on sys_user_permission.project_id=sys_project.id
                    where sys_user_permission.is_delete=0 and sys_user_info.username=%s
                    and sys_project.id=%s and sys_project.is_delete=0"""

PROJECT_LIST_LIKE = """select sys_project.id, project_name, project_desc from sys_project
                 left join sys_user_permission on sys_user_permission.project_id=sys_project.id
                 left join sys_user_info on sys_user_info.id=sys_user_permission.user_id 
                 where sys_user_info.username='%s' and sys_user_permission.is_delete=0
                 and sys_user_info.is_delete=0 and sys_project.is_delete=0 and project_name like '%%%s%%' order by sys_project.create_time desc"""
# TODO 环境模块
# 环境模块
PROJECT_ENV_LIST = """select sys_env.id,sys_env.env_name from sys_env left join sys_user_permission on 
                sys_env.project_id=sys_user_permission.project_id
                 left join sys_user_info on sys_user_info.id=sys_user_permission.user_id  where subsystem_id=%s
                 and sys_env.is_delete=0 and sys_user_info.username=%s"""

# 环境模糊查询
ENV_LIST_LIKE = """select  sys_env.id, sys_project.id, project_name, env_name, host, port, env_desc,
                sys_env.username, DATE_FORMAT(sys_env.create_time, '%%Y-%%m-%%d %%H:%%i:%%S'),creator  from sys_user_permission 
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                left join sys_project on sys_project.id=sys_user_permission.project_id
                left join sys_env on sys_env.project_id=sys_user_permission.project_id
                where sys_user_info.username='%s' and sys_env.is_delete=0 and sys_user_permission.is_delete=0 and 
                env_name like '%%%s%%'  and case when not '%s' then 1 else sys_env.subsystem_id='%s' end 
                and case when not '%s' then 1 else sys_project.id='%s' end 
                order by sys_env.create_time desc"""

# #环境模块 项目权限
ENV_PROJECT_LIST = """select DISTINCT sys_project.id, project_name from sys_user_permission 
                            left join sys_project on project_id=sys_project.id 
                            left join sys_user_info on sys_user_info.id=user_id
                            where sys_project.is_delete=0 and sys_user_permission.is_delete=0 and sys_user_info.username=%s
                            order by sys_project.id desc """
# 环境模块  环境操作权限
ENV_OPERATE = """select sys_env.id from sys_user_permission
                left join sys_project on sys_user_permission.project_id=sys_project.id
                left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                left join sys_env on sys_env.project_id=sys_project.id
                where sys_user_permission.is_delete=0 and sys_user_info.username=%s and sys_env.id=%s and sys_env.is_delete=0"""

# 数据库驱动 数据库环境操作权限
DB_ENV_OPERATE = """select sys_db_env.id from sys_user_permission
                left join sys_project on sys_user_permission.project_id=sys_project.id
                left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                left join sys_db_env on sys_db_env.project_id=sys_project.id
                where sys_user_permission.is_delete=0 and sys_user_info.username=%s and sys_db_env.id=%s and sys_db_env.is_delete=0"""

# #指定环境信息
GET_ONE_ENV = """select sys_env.id, env_name, sys_project.id, project_name, subsystem_name, host, port, env_desc 
                from sys_user_permission 
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                left join sys_project on sys_project.id=sys_user_permission.project_id
                left join sys_subsystem on sys_subsystem.project_id = sys_project.id
                left join sys_env on sys_env.subsystem_id = sys_subsystem.id
                where sys_user_info.username=%s and sys_env.is_delete=0 and sys_user_permission.is_delete=0 and sys_env.id=%s
                """

# # 个人项目权限
GET_PERSON_PROJECT = """select sys_user_permission.project_id from sys_user_permission 
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    left join sys_project on sys_project.id=sys_user_permission.project_id
                    where sys_user_info.username=%s and sys_project.id=%s and sys_user_permission.is_delete=0
                    and sys_user_info.is_delete=0 
                    """

# 个人版本操作权限
GET_PERSON_VERSION = """select sys_subsystem.id from sys_user_permission
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    left join sys_subsystem on  sys_subsystem.project_id = sys_user_permission.project_id
                    where sys_user_info.username=%s and sys_subsystem.id=%s and sys_user_permission.is_delete=0
                    and sys_user_info.is_delete=0 
                    """
# 个人模块操作权限
GET_PERSON_MODULE = """select sys_module.id from sys_user_permission
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    left join sys_subsystem on  sys_subsystem.project_id = sys_user_permission.project_id
                    left join sys_module on sys_module.subsystem_id = sys_subsystem.id 
                    where sys_user_info.username=%s and sys_module.id=%s and sys_user_permission.is_delete=0
                    and sys_user_info.is_delete=0 and sys_module.is_delete=0
                    """
# 数据库权限
GET_PERSON_DATABASE_ENV = """select sys_db_env.project_id from sys_user_permission
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    left join sys_db_env on sys_db_env.project_id=sys_user_permission.project_id
                    where sys_user_info.username=%s and sys_db_env.id=%s and sys_user_permission.is_delete=0"""

GET_PERSON_DATABASE_STATEMENT = """select sys_db_env.project_id from sys_user_permission 
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    left join sys_db_env on sys_db_env.project_id=sys_user_permission.project_id
                    left join sys_db_sqldetail on sys_db_env.id=env_id
                    where sys_user_info.username=%s and sys_db_sqldetail.id=%s and
                    sys_user_permission.is_delete=0 and sys_db_sqldetail.is_delete=0"""

# TODO 接口模块
# 接口模块接口列表
INTERFACE_LIST_LIKE = """select inte_interface.id ,inte_interface.interface_name, inte_interface.req_path, 
                        inte_interface.req_method, inte_interface.state,
                        inte_interface.username, DATE_FORMAT(inte_interface.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'),
                         sum(case when inte_case.case_type=1 and inte_case.is_delete=0 and inte_case.state=1 then 1 else 0 end)
                         ,inte_interface.creator
                        from inte_interface
                        left join inte_case on inte_interface.id=inte_case.interface_id
                        left join sys_subsystem on sys_subsystem.id=inte_interface.subsystem_id
                        left join sys_user_permission on sys_user_permission.project_id=sys_subsystem.project_id
                        left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                        where sys_user_info.username='%s' and inte_interface.is_delete=0 and 
                        sys_user_permission.is_delete=0 
                        and CONCAT(inte_interface.interface_name,  inte_interface.req_path) like '%%%s%%'
                        and sys_subsystem.id='%s' and case when %s=2 then 1 else inte_interface.state=%s end
                        group by inte_interface.id
                        order by inte_interface.id desc
                        """

# 指定版本接口下拉框列表
INTERFACE_LIST = """select inte_interface.id, interface_name, req_path, inte_interface.state from sys_user_permission
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    left join sys_subsystem on sys_subsystem.project_id=sys_user_permission.project_id
                    left join inte_interface on inte_interface.subsystem_id=sys_subsystem.id
                    where sys_user_info.is_delete=0 and sys_user_permission.is_delete=0 and sys_subsystem.is_delete=0
                    and inte_interface.is_delete=0 and sys_user_info.username='%s' and subsystem_id=%s and 
                    inte_interface.state=1"""
# 指定接口信息
SELECT_INTERFACE_INFO = """select distinct inte_interface.id, interface_name, req_path, req_method, 
                    req_headers, req_param, req_body, req_file, extract_list, except_list,sys_project.id ,
                    project_name, sys_subsystem.id, subsystem_name, env_id
                    from inte_interface 
                    left join sys_subsystem on sys_subsystem.id=inte_interface.subsystem_id
                    left join sys_project on sys_subsystem.project_id=sys_project.id 
                    left join sys_user_permission on sys_user_permission.project_id=sys_project.id
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    left join sys_env on sys_env.subsystem_id=sys_subsystem.id
                    where sys_user_info.username=%s and inte_interface.is_delete=0 and sys_user_permission.is_delete=0  
                    and sys_project.is_delete=0 and sys_subsystem.is_delete=0 
                    and inte_interface.id=%s"""

# TODO 用例模块
# 用例模块  用例列表

# 用例模块模糊查询

# 指定用例信息
SELECT_CASE_INFO = """select inte_case.id, inte_case.interface_id, case_name, 
                    inte_case.req_path, inte_case.req_method, 
                    inte_case.req_headers, inte_case.req_param,inte_case.req_body, inte_case.req_file, inte_case.extract_list,
                    inte_case.except_list , run_time, wait_time, sys_module.id from inte_case 
                    left join `sys_module` on `sys_module`.id=inte_case.module_id
                    left join sys_subsystem on sys_subsystem.id=sys_module.subsystem_id
                    left join sys_user_permission on `sys_subsystem`.project_id=sys_user_permission.project_id
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    where sys_user_info.username=%s and inte_case.is_delete=0 and sys_user_permission.is_delete=0 and 
                    inte_case.id=%s"""

# 用例接口环境信息
CASE_ENV_INFO = """select sys_env.`host`, sys_env.`port` from sys_env
                    left join `sys_module` on `sys_module`.env_id=sys_env.id
                    left join inte_case on inte_case.module_id=`sys_module`.id 
                    where inte_case.id=%s and sys_env.is_delete=0 and `inte_case`.is_delete=0"""

CHECK_CASE_NAME_EXIST = """select inte_case.id from inte_case 
                    left join `sys_module` on `sys_module`.id=inte_case.module_id 
                    left join sys_subsystem on sys_subsystem.id=sys_module.subsystem_id
                    where `sys_subsystem`.id=%s and inte_case.is_delete=0 and case_name='%s'
                    and sys_module.is_delete=0 and sys_subsystem.is_delete=0"""

CASE_NAME_OTHER_EXIST = """select inte_case.id from inte_case 
                    left join `sys_module` on `sys_module`.id=inte_case.module_id 
                    left join sys_subsystem on sys_subsystem.id=sys_module.subsystem_id
                    where `sys_subsystem`.id=%s and inte_case.is_delete=0 and case_name=%s
                    and sys_module.is_delete=0 and sys_subsystem.is_delete=0 and inte_case.id!=%s"""

SELECT_MODULE_LIST = """select id, case_list, parent_id from sys_module where subsystem_id=%s and module_type=%s and is_delete=0"""

SELECT_NO_MODULE_LIST = """select id, case_list, parent_id from sys_module where subsystem_id=%s and is_delete=0"""

# TODO 用例导出
SELECT_SUBSYSTEM_CASE = """select a.case_name,a.req_path,a.req_method,a.req_headers,a.req_param,a.req_body,a.req_file,
			a.extract_list,a.except_list,a.run_time,a.wait_time,sys_project.project_name,
			sys_subsystem.subsystem_name,inte_interface.interface_name,inte_interface.req_path,
			sys_module.module_name,a.case_type,a.username,a.state from inte_case a
			left join inte_interface on a.interface_id=inte_interface.id
			left join sys_module on a.module_id=sys_module.id
			left join sys_subsystem on sys_module.subsystem_id=sys_subsystem.id
			left join sys_project on sys_subsystem.project_id=sys_project.id
			where a.is_delete=0 and sys_subsystem.id=%s"""

# TODO 接口导出
SELECT_SUBSYSTEM_INTERFACE = """select a.interface_name,a.req_path,a.req_method,a.req_headers,a.req_param,a.req_body,
			a.req_file,a.extract_list,a.except_list,sys_project.project_name,sys_subsystem.subsystem_name,
			sys_env.env_name,sys_env.`host`,sys_env.`port`,a.username,a.state,
			sum(case when inte_case.case_type=1 and inte_case.is_delete=0 and inte_case.state=1 then 1 else 0 end)	
			from inte_interface a
			left join inte_case on a.id=inte_case.interface_id
			left join sys_subsystem on a.subsystem_id=sys_subsystem.id
			left join sys_project on sys_subsystem.project_id=sys_project.id
			left join sys_env on a.env_id=sys_env.id
			where a.is_delete=0 and sys_subsystem.id='%s'  
		    group by a.id
			order by a.id desc"""

# TODO 导出报告
EXPORT_REPORT = """select inte_task.task_name,inte_report.report_path,inte_report.username from inte_report
                left join inte_task on inte_report.task_id=inte_task.id
                WHERE inte_task.is_delete=0 and inte_report.is_delete=0 and inte_task.project_id=%s"""
# TODO 导出任务报告
EXPORT_REPORT_TASK = """select inte_task.task_name,inte_report.report_path,inte_report.username from inte_report
                left join inte_task on inte_report.task_id=inte_task.id
                WHERE inte_task.is_delete=0 and inte_report.is_delete=0 and inte_report.task_id=%s"""

# 用例接口列表
# , inte_case.req_headers,  inte_case.req_param, inte_case.req_body, inte_case.req_file,  inte_case.except_list,
# 优化前
# SELECT_CASE_LIST = """select a.id,a.case_name, a.req_path, a.req_method, a.extract_list, a.updatetime, a.username, a.state
#                     from (select inte_case.id,case_name, inte_case.req_path, inte_case.req_method,
#                     DATE_FORMAT(inte_case.update_time,'%%Y-%%m-%%d %%H:%%i:%%S') updatetime, inte_case.username,
#                     inte_case.state, IFNULL(GROUP_CONCAT(inte_extract.param_name) ,'')extract_list, module_id
#                     from inte_case left join inte_extract on find_in_set(inte_extract.id,inte_case.extract_list)
#                     where inte_case.is_delete=0  group by inte_case.id) a
#                     left join `sys_module` on `sys_module`.id=a.module_id
#                     left join sys_subsystem on sys_module.subsystem_id=sys_subsystem.id
#                     left join sys_user_permission on sys_user_permission.project_id=`sys_subsystem`.project_id
#                     left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
#                     where sys_user_permission.is_delete=0 and sys_user_info.username='%s'
#                     and `sys_module`.is_delete=0 and case when %s = 2 then 1 else a.state=%s end
#                     and sys_module.module_type=%s
#                     and a.id in (%s) order by find_in_set (a.id, '%s')"""
# 优化后
SELECT_CASE_LIST = """select a.id,a.case_name, a.req_path, a.req_method, 
                    IFNULL(GROUP_CONCAT(inte_extract.param_name) ,'') extract_list, a.updatetime, a.username, a.state,a.creator 
                    from (select inte_case.id,case_name, inte_case.req_path, inte_case.req_method, 
                    DATE_FORMAT(inte_case.update_time,'%%Y-%%m-%%d %%H:%%i:%%S') updatetime, inte_case.username, 
                    inte_case.state, module_id ,extract_list,inte_case.creator
                    from inte_case 
                    left join `sys_module` on `sys_module`.id=inte_case.module_id
                    left join sys_subsystem on sys_module.subsystem_id=sys_subsystem.id
                    left join sys_user_permission on sys_user_permission.project_id=`sys_subsystem`.project_id
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    where sys_user_permission.is_delete=0 and sys_user_info.username='%s' 
                    and `sys_module`.is_delete=0 and case when %s = 2 then 1 else inte_case.state=%s end
                    and sys_module.module_type=%s
                    and inte_case.id in (%s)) a
                    left join inte_extract on find_in_set(inte_extract.id,a.extract_list) 
                    group by a.id  order by find_in_set (a.id, '%s')"""
SELECT_CASE_LIST_NOTYPE = """select a.id,a.case_name, a.req_path, a.req_method, 
                    IFNULL(GROUP_CONCAT(inte_extract.param_name) ,'') extract_list, a.updatetime, a.username, a.state,a.creator 
                    from (select inte_case.id,case_name, inte_case.req_path, inte_case.req_method, 
                    DATE_FORMAT(inte_case.update_time,'%%Y-%%m-%%d %%H:%%i:%%S') updatetime, inte_case.username, 
                    inte_case.state, module_id ,extract_list,inte_case.creator
                    from inte_case 
                    left join `sys_module` on `sys_module`.id=inte_case.module_id
                    left join sys_subsystem on sys_module.subsystem_id=sys_subsystem.id
                    left join sys_user_permission on sys_user_permission.project_id=`sys_subsystem`.project_id
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    where sys_user_permission.is_delete=0 and sys_user_info.username='%s' 
                    and `sys_module`.is_delete=0 and case when %s = 2 then 1 else inte_case.state=%s end
                    and inte_case.id in (%s)) a
                    left join inte_extract on find_in_set(inte_extract.id,a.extract_list) 
                    group by a.id  order by find_in_set (a.id, '%s')"""

# 用例模块模糊查询
# 优化前
# CASE_LIST_LIKE = """select a.id,a.case_name, a.req_path, a.req_method, a.extract_list, a.updatetime, a.username, a.state
#                     from (select inte_case.id,case_name, inte_case.req_path, inte_case.req_method,
#                     DATE_FORMAT(inte_case.update_time,'%%Y-%%m-%%d %%H:%%i:%%S') updatetime, inte_case.username,
#                     inte_case.state, IFNULL(GROUP_CONCAT(inte_extract.param_name) ,'')extract_list, module_id
#                     from inte_case left join inte_extract on find_in_set(inte_extract.id,inte_case.extract_list)
#                      where inte_case.is_delete=0  group by inte_case.id) a
#                     left join `sys_module` on `sys_module`.id=a.module_id
#                     left join sys_subsystem on sys_module.subsystem_id=sys_subsystem.id
#                     left join sys_user_permission on sys_user_permission.project_id=`sys_subsystem`.project_id
#                     left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
#                     where sys_user_permission.is_delete=0 and sys_user_info.username='%s'
#                     and `sys_module`.is_delete=0 and `sys_subsystem`.id=%s and sys_module.module_type=%s and
#                      CONCAT(a.case_name, a.req_path,a.extract_list) like '%%%s%%' and case when %s = 2 then 1 else a.state=%s end"""

# TODO 区分模块类型，前置-后置-普通
CASE_LIST_LIKE = """select b.id,b.case_name, b.req_path,b.req_method, b.extract_list, b.updatetime, b.username, b.state,b.creator
                     from(
                    select a.id,a.case_name, a.req_path, a.req_method, IFNULL(GROUP_CONCAT(inte_extract.param_name) ,'')
                        extract_list, a.updatetime, a.username, a.state,a.creator
                    from (
                    select inte_case.id,case_name, inte_case.req_path, inte_case.req_method, 
                    DATE_FORMAT(inte_case.update_time,'%%Y-%%m-%%d %%H:%%i:%%S') updatetime, inte_case.username, 
                    inte_case.state,extract_list, module_id,inte_case.creator
                    from inte_case left join `sys_module` on `sys_module`.id=inte_case.module_id
                    left join sys_subsystem on sys_module.subsystem_id=sys_subsystem.id
                    left join sys_user_permission on sys_user_permission.project_id=`sys_subsystem`.project_id
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    where sys_user_permission.is_delete=0 and sys_user_info.username='%s' 
                    and `sys_module`.is_delete=0 and `sys_subsystem`.id=%s
                    and sys_module.module_type=%s and case when %s = 2 then 1 else inte_case.state=%s end 
                    and inte_case.is_delete=0) a 
                    left join inte_extract on find_in_set(inte_extract.id,a.extract_list) group by a.id)b 
                    where CONCAT(b.case_name, b.req_path, b.extract_list) like '%%%s%%'"""
# TODO 不区分模块类型
CASE_LIST_LIKE_NOTYPE = """select b.id,b.case_name, b.req_path,b.req_method, b.extract_list, b.updatetime, b.username, b.state,b.creator
                     from(
                    select a.id,a.case_name, a.req_path, a.req_method, IFNULL(GROUP_CONCAT(inte_extract.param_name) ,'')
                        extract_list, a.updatetime, a.username, a.state,a.creator
                    from (
                    select inte_case.id,case_name, inte_case.req_path, inte_case.req_method, 
                    DATE_FORMAT(inte_case.update_time,'%%Y-%%m-%%d %%H:%%i:%%S') updatetime, inte_case.username, 
                    inte_case.state,extract_list, module_id,inte_case.creator
                    from inte_case left join `sys_module` on `sys_module`.id=inte_case.module_id
                    left join sys_subsystem on sys_module.subsystem_id=sys_subsystem.id
                    left join sys_user_permission on sys_user_permission.project_id=`sys_subsystem`.project_id
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    where sys_user_permission.is_delete=0 and sys_user_info.username='%s' 
                    and `sys_module`.is_delete=0 and `sys_subsystem`.id=%s
                    and case when %s = 2 then 1 else inte_case.state=%s end 
                    and inte_case.is_delete=0) a 
                    left join inte_extract on find_in_set(inte_extract.id,a.extract_list) group by a.id)b 
                    where CONCAT(b.case_name, b.req_path, b.extract_list) like '%%%s%%'"""

# 指定接口的提取规则
SELECT_INTERFACE_EXTRACT_LIST = """select id, param_name, rule, data_format from inte_extract where id in %s"""

SELECT_INTERFACE_EXTRACT_LIST2 = """select param_name, rule, data_format from inte_extract where id in %s"""

# 指定提取规则参数的id
# SELECT_PUBLIC_PARAM_ID = """select id from inte_extract where project_id=%s and `param_name` in %s"""

SELECT_EXTRACT_ID = """select id from inte_extract where project_id=%s and `param_name` in %s"""

# 执行用例的列表
EXECUTE_CASE_LIST = """select inte_case.id, case_name, sys_module.id, module_name, sys_env.host, sys_env.port,
                        inte_case.req_method, inte_case.req_path, inte_case.req_headers, inte_case.req_param,
                        inte_case.req_body, inte_case.req_file, inte_case.extract_list, inte_case.except_list, 
                        `sys_module`.subsystem_id, run_time, module_type, interface_id, sys_user_permission.project_id
                        ,inte_case.wait_time
                        from `sys_module`
                        left join inte_case on `sys_module`.id=inte_case.module_id
                        left join sys_env on `sys_module`.env_id=sys_env.id
                        left join sys_subsystem on sys_subsystem.id=sys_module.subsystem_id
                        left join sys_user_permission on sys_subsystem.project_id=sys_user_permission.project_id
                        left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                        where `sys_module`.is_delete=0 and inte_case.is_delete=0 and sys_user_permission.is_delete=0 
                        and sys_user_info.username='%s' and inte_case.state=1 and inte_case.id in (%s)
                        order by find_in_set (inte_case.id, '%s')"""

# TODO 数据库环境模块
DATABASE_ENV_LIST = """select sys_db_env.id, project_name, db_type, env_ip, env_name, env_port, `user`, sys_db_env.`password`, dbname,
                env_desc, DATE_FORMAT(sys_db_env.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), sys_db_env.username from sys_db_env 
                left join sys_user_permission on sys_db_env.project_id=sys_user_permission.project_id
                left join sys_project on sys_db_env.project_id=sys_project.id
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                where sys_user_info.is_delete=0 and sys_user_permission.is_delete=0 and sys_db_env.is_delete=0 and sys_project.is_delete=0
                and sys_user_info.username=%s """

DATABASE_ENV_LIST_LIKE = """select sys_db_env.id, project_name, db_type, env_ip, env_name, env_port, `user`, 
                sys_db_env.`password`, dbname, env_desc, 
                DATE_FORMAT(sys_db_env.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), sys_db_env.username,sys_db_env.creator
                from sys_db_env 
                left join sys_user_permission on sys_db_env.project_id=sys_user_permission.project_id
                left join sys_project on sys_db_env.project_id=sys_project.id
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                where sys_user_info.is_delete=0 and sys_user_permission.is_delete=0 and sys_db_env.is_delete=0 and sys_project.is_delete=0
                and sys_user_info.username='%s' and env_name like '%%%s%%' and sys_project.id=%s order by sys_db_env.id desc"""

SELECT_DATABASE_ENV_INFO = """select sys_db_env.id, sys_db_env.project_id, db_type, env_ip, env_name, env_port, `user`, sys_db_env.`password`, dbname,  env_desc, 
                DATE_FORMAT(sys_db_env.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), sys_db_env.username from sys_db_env 
                left join sys_user_permission on sys_db_env.project_id=sys_user_permission.project_id
                left join sys_project on sys_db_env.project_id=sys_project.id
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                where sys_user_info.is_delete=0 and sys_user_permission.is_delete=0 and sys_db_env.is_delete=0 and sys_project.is_delete=0
                and sys_user_info.username=%s and sys_db_env.id=%s"""

SQL_LIST_LIKE = """select sys_db_sqldetail.id, sql_name, `sql`,
                sys_db_sqldetail.`state`, result, DATE_FORMAT(sys_db_sqldetail.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), 
                sys_db_sqldetail.username, remark
                from sys_db_sqldetail 
                left join sys_db_env on sys_db_sqldetail.env_id=sys_db_env.id
                left join sys_user_permission on sys_db_env.project_id=sys_user_permission.project_id
                left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                where sys_db_sqldetail.is_delete=0 and sys_user_permission.is_delete=0 and sys_db_env.is_delete=0
                and sys_user_info.is_delete=0 and sys_user_info.username='%s' 
                and sql_name like '%%%s%%' and sys_db_env.id=%s"""

SQL_DETAIL_INFO = """select sys_db_sqldetail.id, sql_name, `sql` ,remark, result
            from sys_db_sqldetail left join sys_db_env on sys_db_sqldetail.env_id=sys_db_env.id
            left join sys_user_permission on sys_db_env.project_id=sys_user_permission.project_id
            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
            where sys_db_sqldetail.is_delete=0 and sys_user_permission.is_delete=0
            and sys_user_info.is_delete=0 and sys_user_info.username=%s and sys_db_sqldetail.id=%s"""

SELECT_DATABASE_STATEMENT_INFO = """select sys_db_sqldetail.id, env_id, env_name, db_type, env_ip, env_port, `user`, 
            sys_db_env.`password`, dbname, sql_name, `sql` 
            from sys_db_sqldetail left join sys_db_env on sys_db_sqldetail.env_id=sys_db_env.id
            left join sys_user_permission on sys_db_env.project_id=sys_user_permission.project_id
            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
            where sys_db_sqldetail.is_delete=0 and sys_user_permission.is_delete=0
            and sys_user_info.is_delete=0 and sys_user_info.username=%s and sys_db_sqldetail.id=%s"""

# TODO 接口执行
EXECUTE_INTERFACE = """select inte_interface.id, interface_name, host, port, req_path, 
                    req_method, req_headers, req_param, 
                    inte_interface.project_id, project_name, inte_interface.env_id, req_body, req_file, extract_list, except_list
                    from inte_interface left join sys_env on env_id=sys_env.id 
                    left join sys_project on sys_project.id=interface.project_id
                    left join sys_user_permission on inte_interface.project_id=sys_user_permission.project_id
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    where inte_interface.is_delete=0 and sys_project.is_delete=0 and 
                    sys_user_permission.is_delete=0 and sys_user_info.username=%s and inte_interface.id=%s"""
# 执行用例接口
EXECUTE_CASE_INTERFACE = '''select inte_case.id, inte_interface.interface_name, sys_env.host,
                sys_env.port, inte_case.req_path, 
                inte_case.req_method, inte_case.req_headers, inte_case.req_param,
                sys_env.project_id, project_name, sys_env.id, inte_case.req_body, 
                inte_case.req_file, inte_case.extract_list, inte_case.except_list 
                from inte_case left join `case` on inte_case.case_id=`case`.id
                left join sys_env on sys_env.id=`case`.env_id
                left join inte_interface on inte_case.interface_id=interface.id
                left join sys_project on sys_env.project_id=sys_project.id
                left join sys_user_permission on sys_user_permission.project_id=sys_env.project_id
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                where inte_case.is_delete=0 and sys_project.is_delete=0 and sys_user_permission.is_delete=0
                and sys_user_info.is_delete=0 and sys_user_info.username=%s and  inte_case.id=%s '''

# TODO 接口执行

# TODO 任务管理
TASK_ENV_INFO = """select host, port from inte_task_case 
                    left join sys_env on sys_env.id=inte_task_case.env_id
                    where
                    inte_task_case.id=%s and sys_env.is_delete=0"""

TASK_LIST_LIKE = """select `inte_task`.id, `inte_task`.task_name, task_desc, cron, inte_task.state, `inte_task`.username, 
                DATE_FORMAT(`inte_task`.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), project_name, sys_project.id,
                 inte_task.excel_file_name,inte_task.creator,a.case_count from `inte_task`
                left join (select count(id) case_count,task_id from inte_task_case where is_delete=0 
                group by task_id) a on inte_task.id=a.task_id
                left join sys_project on sys_project.id=inte_task.project_id
                left join sys_user_permission on sys_project.id=sys_user_permission.project_id
                left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                where `inte_task`.is_delete=0 and sys_project.is_delete=0 and sys_user_info.is_delete=0 and sys_user_info.username='%s'
                and `inte_task`.task_name like '%%%s%%' and case when not %s then 1 else inte_task.project_id=%s 
                end and sys_user_permission.is_delete=0
                order by `inte_task`.id desc"""

# ！！！未加权限
TASK_CASE_LIST = """select a.id, a.case_id, a.case_name, a.req_path, a.req_method,a.extract_list,
                a.state, sys_module.subsystem_id, case when sys_module.module_type=1 then '普通用例' when sys_module.module_type=2 then '前置用例' when sys_module.module_type=3 then '后置用例' end from (
                select it.id, it.case_id, it.case_name, it.req_path, it.req_method, 
                IFNULL(GROUP_CONCAT(inte_extract.param_name) ,'') extract_list, it.state
                from inte_task_case as it left join inte_extract on find_in_set(inte_extract.id,it.extract_list)
                where it.is_delete=0 and it.task_id=%s group by it.id) a									
                left join inte_case on a.case_id=inte_case.id
                left join sys_module on inte_case.module_id=sys_module.id
                where a.case_id in (%s) and case when not %s then 1 else sys_module.module_type=%s end 
                and CONCAT(a.case_name, a.req_path,a.extract_list) like '%%%s%%' and case when %s=2 then 1 else a.state=%s end 
                order by find_in_set(a.case_id, '%s')"""
# and module_type = 1
# 任务用例新增时查询用例表
TASK_CASE_ADD_LIST = """select inte_case.id, case_name,req_path,
            req_method, req_headers, req_param, req_body, req_file, extract_list,
            except_list, run_time, wait_time, env_id, state
            from inte_case 
            left join sys_module on sys_module.id=inte_case.module_id
            where inte_case.is_delete = 0 and inte_case.id in (%s) order by find_in_set(inte_case.id, '%s') """

# 指定任务用例接口信息
SELECT_TASK_CASE_INFO = """select inte_task_case.id, interface_name, inte_task_case.case_name, inte_task_case.req_path,
                inte_task_case.req_method, inte_task_case.req_headers, inte_task_case.req_param, 
                inte_task_case.req_body, inte_task_case.req_file,inte_task_case.extract_list, 
                inte_task_case.except_list, inte_task_case.run_time , inte_task_case.wait_time
                from inte_task_case
                left join inte_case on inte_case.id=inte_task_case.case_id 
                left join inte_interface on inte_case.interface_id=inte_interface.id
                left join sys_subsystem on sys_subsystem.id=inte_interface.subsystem_id
                left join sys_user_permission on sys_user_permission.project_id=sys_subsystem.project_id
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                where sys_user_info.username=%s and sys_user_permission.is_delete=0 and inte_task_case.is_delete=0 and 
                inte_task_case.id=%s"""

SELECT_TASK_CASE_INFO_TREE = """select inte_task_case.id, interface_name, inte_task_case.case_name, inte_task_case.req_path,
                inte_task_case.req_method, inte_task_case.req_headers, inte_task_case.req_param, 
                inte_task_case.req_body, inte_task_case.req_file,inte_task_case.extract_list, 
                inte_task_case.except_list, inte_task_case.run_time , inte_task_case.wait_time
                from inte_task_case
                left join inte_case on inte_case.id=inte_task_case.case_id 
                left join inte_interface on inte_case.interface_id=inte_interface.id
                left join sys_subsystem on sys_subsystem.id=inte_interface.subsystem_id
                left join sys_user_permission on sys_user_permission.project_id=sys_subsystem.project_id
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                where sys_user_info.username=%s and sys_user_permission.is_delete=0 and inte_task_case.is_delete=0 and 
                inte_task_case.case_id=%s and task_id=%s"""

# 指定用例接口信息
TASK_CASE_INFO = """select inte_case.id, interface_name, inte_case.case_name, inte_case.req_path,
                inte_case.req_method, inte_case.req_headers, inte_case.req_param, 
                inte_case.req_body, inte_case.req_file,inte_case.extract_list, 
                inte_case.except_list, inte_case.run_time , inte_case.wait_time
                from inte_case
                left join inte_interface on inte_interface.id=inte_case.interface_id
                left join sys_subsystem on sys_subsystem.id=inte_interface.subsystem_id
                left join sys_user_permission on sys_user_permission.project_id=sys_subsystem.project_id
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                where sys_user_info.username=%s and inte_case.is_delete=0 and sys_user_permission.is_delete=0 and 
                inte_case.id=%s"""

# 查询指定用例列表
CASE_LIST = """select inte_case.id, case_name, inte_case.module_id, 3, '' from inte_case
                where inte_case.is_delete=0 and inte_case.id in (%s) order by  find_in_set(inte_case.id, '%s')
                """

# 获取模块路径
MODULE_PATH = """select subsystem_name from sys_subsystem
                where sys_subsystem.id=%s and sys_subsystem.is_delete=0"""

# 查询modoul数据
MODULE_LIST = """select sys_module.id, sys_module.module_name
                from `sys_module` 
                left join sys_subsystem on sys_subsystem.id=sys_module.subsystem_id
                left join sys_user_permission on sys_user_permission.project_id=sys_subsystem.project_id
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                where sys_user_info.is_delete=0 and sys_user_permission.is_delete=0 and `sys_module`.is_delete=0 
                and sys_user_info.username=%s and `sys_module`.subsystem_id=%s """

MODULE_LIST_TREE = """select sys_module.id, sys_module.module_name, parent_id, case when module_type=1 then 2 else 1 end,
                report_path, module_type
                from `sys_module` 
                left join sys_subsystem on sys_subsystem.id=sys_module.subsystem_id
                left join sys_user_permission on sys_user_permission.project_id=sys_subsystem.project_id
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                where sys_user_info.is_delete=0 and sys_user_permission.is_delete=0 and `sys_module`.is_delete=0 
                and sys_user_info.username=%s and `sys_module`.subsystem_id=%s order by sys_module.create_time"""

EXECTUE_TASK = """select itc.id, itc.case_name, sm.id, module_name, se.host, se.port,
                itc.req_method, itc.req_path, itc.req_headers, itc.req_param,
                itc.req_body, itc.req_file, itc.extract_list, itc.except_list, %s interface_count,
                sm.subsystem_id, itc.run_time, itc.wait_time,  module_type, interface_id, sys_user_permission.project_id, 'task'
                from `inte_task` it
                left join inte_task_case itc on it.id=itc.task_id
                left join inte_case ic on itc.case_id=ic.id
                left join sys_module sm on ic.module_id=sm.id
                left join sys_env se on itc.env_id=se.id
                left join sys_subsystem ss on ss.id=sm.subsystem_id
                left join sys_user_permission on ss.project_id=sys_user_permission.project_id
                left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                where sm.is_delete=0 and ic.is_delete=0 and sys_user_permission.is_delete=0 
                and sys_user_info.username='%s' and itc.state=1 and itc.is_delete=0 and it.id=%s
                and itc.case_id in (%s) order by find_in_set (itc.case_id, '%s')"""

BAT_EXECTUE_TASK = """select itc.id, itc.case_name, sm.id, module_name,
                itc.req_method, itc.req_path, itc.req_headers, itc.req_param,
                itc.req_body, itc.req_file, itc.extract_list, itc.except_list, %s interface_count,
                sm.subsystem_id, itc.run_time, itc.wait_time,  module_type, interface_id, sys_user_permission.project_id, 'task'
                from `inte_task` it
                left join inte_task_case itc on it.id=itc.task_id
                left join inte_case ic on itc.case_id=ic.id
                left join sys_module sm on ic.module_id=sm.id
                left join sys_subsystem ss on ss.id=sm.subsystem_id
                left join sys_user_permission on ss.project_id=sys_user_permission.project_id
                left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                where sm.is_delete=0 and ic.is_delete=0 and sys_user_permission.is_delete=0 
                and sys_user_info.username='%s' and itc.state=1 and itc.is_delete=0 and it.id=%s
                and itc.case_id in (%s) order by find_in_set (itc.case_id, '%s')"""
# TODO 报告
REPORT_LIST_LIKE = """select inte_report.id, task_name,report_path, file_name, case when inte_report.report_type
                    then '接口执行' else '平台执行' end ,
                    DATE_FORMAT(inte_report.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), 
                    inte_report.username from `inte_report` 
                    left join `inte_task` on `inte_task`.id=`inte_report`.task_id 
                    left join sys_user_permission on sys_user_permission.project_id=inte_task.project_id
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id 
                    where sys_user_info.username='%s' and inte_report.is_delete=0
                    and task_name like '%%%s%%' and inte_task.project_id=%s
                    ORDER BY inte_report.update_time desc
            """

# TODO 任务报告
TASK_REPORT_LIST = """select inte_report.id, task_name, report_path, file_name, case when inte_report.report_type then '接口执行' else '平台执行' end ,
                    DATE_FORMAT(inte_report.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), 
                    inte_report.username from `inte_report` left join `inte_task` on `inte_task`.id=`inte_report`.task_id 
                    where inte_report.is_delete=0
                    and inte_task.id=%s ORDER BY inte_report.update_time desc"""

# TODO 用例报告
CASE_REPORT_LIST = """select report.id, case_name, CASE WHEN report_type=1 THEN '用例' END r_type, report_path,
         file_name, DATE_FORMAT(report.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), 
         report.username from `report` left join `case` on `case`.id=`report`.case_id where report.is_delete=0 and 
         case.id=%s ORDER BY report.update_time desc"""
# TODO 接口记录
INTERFACE_RECORD = """select interface_record.id,  interface_name, project_name, host, port, req_path, req_method, 
            req_headers, req_param, req_body, req_file, resp_code, resp_result, extract_name, extract_rule, 
            resp_data, except_result, execute_state, 
            DATE_FORMAT(interface_record.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), interface_record.username,
            extract_list, except_list
            from interface_record left join sys_project on interface_record.project_id=sys_project.id
            where interface_id = %s order by interface_record.create_time desc
            """

# TODO 用例接口记录
CASE_INTERFACE_RECORD = """select interface_record.id,  interface_name, project_name, host, port, req_path, req_method, 
                        req_headers, req_param, req_body, req_file, resp_code, resp_result, extract_name, extract_rule, 
                        resp_data, except_result, execute_state, 
                        DATE_FORMAT(interface_record.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), interface_record.username
                        ,extract_list, except_list
                        from interface_record left join sys_project on interface_record.project_id=sys_project.id
                        where interface_record.inte_case_id=%s order by interface_record.create_time desc
                        """

# TODO 参数管理
PARAM_LIST_LIKE = """select `sys_public_param`.id, param_name, param_desc, rule, `sys_dict`.dict_value, input_params,
                DATE_FORMAT(`sys_public_param`.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), `sys_public_param`.username
                from `sys_public_param` left join `sys_dict` on `sys_public_param`.rule = `sys_dict`.id 
                left join sys_user_permission on sys_user_permission.project_id=`sys_public_param`.project_id 
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id 
                where `sys_public_param`.is_delete=0 and param_type=2 and sys_user_info.username='%s' 
                and sys_user_permission.is_delete=0 and param_name like '%%%s%%' and `sys_public_param`.project_id = %s
                order by sys_public_param.id desc"""

PARAM_INFO = """select id, param_name, param_desc, rule, input_params, project_id from `sys_public_param`
                 where id = %s and is_delete=0"""

# TODO 参数权限校验
PARAM_PERMISSION = """select sys_public_param.id from sys_user_permission
				left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
				left join sys_public_param on sys_public_param.project_id=sys_user_permission.project_id
				where sys_user_permission.is_delete=0 and sys_public_param.is_delete=0 and sys_user_info.is_delete=0 
				and sys_user_info.username=%s and sys_public_param.id=%s"""

# TODO 子系统查询
ENV_SUBSYSTEM_LIST = """select DISTINCT sys_subsystem.id,subsystem_name from user_permission
                        left join sys_subsystem on projectid=sys_subsystem.project_id
                        left join sys_user_info on sys_user_info.id=userid
                        where sys_subsystem.is_delete=0 and user_permission.is_delete=0 and sys_user_info.username=%s"""
# 子系统列表查询
SUBSYSTEM_LIST_LIKE = """select sys_subsystem.id,subsystem_name,subsystem_desc from sys_user_permission 
                        left join sys_subsystem on sys_user_permission.project_id=sys_subsystem.project_id
                        left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                        where sys_subsystem.is_delete=0 and sys_user_permission.is_delete=0 
                        and sys_user_info.username='%s' and subsystem_name like '%%%s%%' and 
                        sys_user_permission.project_id='%s' order by sys_subsystem.create_time desc"""
# 子系统权限校验
SUBSYSTEM_OPERATE = """select sys_subsystem.id from sys_user_permission
                left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                left join sys_subsystem on sys_subsystem.project_id=sys_user_permission.project_id
                where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0 and sys_subsystem.is_delete=0 
                and sys_user_info.username=%s and sys_subsystem.id=%s"""

# 版本列表查询
VERSION_LIST_LIKE = """select sys_version.id,version_name,version_desc from sys_subsystem
                        left join sys_version on sys_subsystem.id=sys_version.subsystem_id
                        left join sys_user_permission on sys_user_permission.project_id=sys_subsystem.project_id
                        left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                        where sys_version.is_delete=0 and sys_subsystem.is_delete=0
                        and sys_subsystem.id='%s' and version_name like '%%%s%%' and sys_user_info.username='%s'
                        order by sys_version.create_time desc
                        """

# 模块列表查询
ENV_MODULE_LIKE = """select sys_module.id,module_name,module_desc,parent_id from sys_version
                    left join sys_module on sys_version.id=sys_module.version_id
                    where sys_version.is_delete=0 and sys_module.is_delete=0 and sys_module.version_id='%s' 
                    and module_name like '%%%s%%'
                    """
# 模块权限校验
MODULE_OPERATE = """select sys_module.id from sys_user_permission
                left join sys_project on sys_user_permission.project_id=sys_project.id
                left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                left join sys_subsystem on sys_subsystem.project_id=sys_project.id
                left join sys_module on sys_module.subsystem_id = sys_subsystem.id
                where sys_user_permission.is_delete=0 and sys_user_info.username='%s' 
                and sys_module.id=%s and sys_module.is_delete=0"""

# 根据模块ID查询用例列表
CASE_MODULE_LIST = """select a.id,a.case_name,a.req_path,a.req_method,a.state,a.username, 
                DATE_FORMAT(a.update_time, '%%Y-%%m-%%d %%H:%%i:%%S') from inte_case a,sys_module b 
                where a.module_id = b.id and a.is_delete=0 and b.is_delete=0 and a.module_id='%s'"""
# 根据版本ID查询出所有模块的用例
CASE_VERSION_LIST = """select a.id,a.case_name,a.req_path,a.req_method,a.state,a.username, 
                DATE_FORMAT(a.update_time, '%%Y-%%m-%%d %%H:%%i:%%S') 
                from inte_case a,sys_module b,sys_version c 
                where c.id = b.version_id and b.id = a.module_id and a.is_delete=0 and b.is_delete=0 
                and c.is_delete=0 and b.version_id='%s'"""

# 查询版本名称和用例列表
NAME_CASE_LIST = """select  a.version_name, b.case_list from sys_module b 
                    left join sys_version a on b.version_id=a.id where 
                    a.is_delete=0 and b.is_delete=0 and b.version_id='%s'"""
# 查询树形图
TREE_CASE_LIST = """select b.id,a.id,b.module_name,a.case_name,b.is_delete,b.module_type,b.parent_id 
                from inte_case a left join sys_module b on b.id = a.module_id 
                where a.is_delete=0 and b.is_delete=0 and a.module_id='%s'"""

# TODO 加密签名
# 获取签名变量列表
ENCRYPTION_LIST = """select sys_encryption.id,variable_name,request_method,url,publickey,
                    plaintext,extract_field,encr_type,sys_encryption.username, 
                    DATE_FORMAT(sys_encryption.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), remark from sys_encryption
                    left join sys_user_permission on sys_user_permission.project_id=sys_encryption.project_id
                    left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                     WHERE sys_encryption.is_delete=0 and sys_user_info.username='%s' 
                     and sys_encryption.project_id='%s' and sys_encryption.variable_name like '%%%s%%'
                     order by sys_encryption.id desc"""
# 加密权限校验
ENCRYPTION_PROMISSION = """select sys_encryption.id from sys_user_permission
				left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
				left join sys_encryption on sys_encryption.project_id=sys_user_permission.project_id
				where sys_user_permission.is_delete=0 and sys_encryption.is_delete=0 and sys_user_info.is_delete=0 
				and sys_user_info.username=%s and sys_encryption.id=%s"""

# TODO 数据驱动管理
DATADRIVEN_LIST_LIKE = """select d.id, d.param_name,d.remark, d.param_list, d.username, 
            DATE_FORMAT(d.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'),d.creator from sys_data_driven d 
            left join sys_user_permission on sys_user_permission.project_id=d.project_id 
            left join sys_user_info on sys_user_info.id=sys_user_permission.user_id 
            where d.is_delete=0 and sys_user_info.username ='%s' and sys_user_permission.is_delete = 0 
            and d.param_name like '%%%s%%' and d.project_id = %s"""

# TODO 数据驱动权限校验
DATADRIVEN_PROMISSION = """select sys_data_driven.id from sys_user_permission
				left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
				left join sys_data_driven on sys_data_driven.project_id=sys_user_permission.project_id
				where sys_user_permission.is_delete=0 and sys_data_driven.is_delete=0 and sys_user_info.is_delete=0 
				and sys_user_info.username=%s and sys_data_driven.id=%s"""

DATADRIVEN_INFO = """select id, param_name, param_list, project_id,remark from `sys_data_driven` where id = %s and is_delete=0"""

# TODO   复制环境
EVN_copy_SQL = """select id,env_name,env_desc,`host`,`port`,project_id,state,username,subsystem_id from sys_env 
             where is_delete=0 and subsystem_id = %s"""

# TODO  复制子系统插入数据库
SUBSYSTEM_SQL = """SELECT subsystem_name,subsystem_desc,username,project_id FROM sys_subsystem WHERE id=%s AND is_delete=0"""
# 查询模块
MODULE_SQL = """SELECT id, module_name,module_desc,module_type,parent_id,subsystem_id,env_id,case_list,sub_module_list,
                username,operater FROM sys_module WHERE subsystem_id = %s AND is_delete=0 order by sys_module.create_time"""
# 查询用例
INTE_CASE_SQL = """SELECT id,case_name,req_path,req_method,req_headers,req_param,req_body,req_file,extract_list,except_list,is_mock,
                       mock_id,run_time,state,excute_result,interface_id,module_id,username,case_type FROM inte_case 
                       WHERE is_delete=0 and id in (%s) order by find_in_set(id,'%s')"""
# 查询接口
INTERFACE_SQL = """SELECT id,interface_name,req_path,req_method,req_headers,req_param,req_body,req_file,extract_list,except_list,state,excute_result,env_id,username,
                        subsystem_id from inte_interface where subsystem_id = %s and is_delete=0"""

# TODO  复制任务插入数据库
TASK_SQL = """select task_name,task_desc,case_list,case_dict,execute_result,cron,project_id,state from inte_task where is_delete=0 and id=%s"""

TASK_CASE_SQL = """select case_id,case_name,req_path,req_method,req_headers,req_param,req_body,req_file,extract_list,except_list,
                            is_mock,mock_id,run_time,state,env_id,excute_result from inte_task_case where 
                            is_delete = 0 and task_id = %s and case_id in (%s) order by find_in_set(case_id,'%s')"""

# 任务权限校验
TASK_PERMISSION = """select inte_task.id from sys_user_permission
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            left join inte_task on inte_task.project_id=sys_user_permission.project_id
                            where sys_user_permission.is_delete=0 and inte_task.is_delete=0 and sys_user_info.is_delete=0 
                            and sys_user_info.username=%s and inte_task.id=%s"""
# 用例权限校验
CASE_PERMISSION = """select inte_case.id from sys_user_permission
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            left join sys_subsystem on sys_subsystem.project_id=sys_user_permission.project_id
                            left join sys_module on sys_module.subsystem_id=sys_subsystem.id
                            left join inte_case on inte_case.module_id=sys_module.id
                            where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0 
                            and sys_subsystem.is_delete=0 and sys_module.is_delete=0 and inte_case.is_delete=0
                            and sys_user_info.username=%s and inte_case.id=%s"""

# 任务用例权限校验
TASK_CASE_PERMISSION = """select inte_task_case.id from sys_user_permission
							left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
							left join inte_task on inte_task.project_id=sys_user_permission.project_id
							left join inte_task_case on inte_task_case.task_id=inte_task.id
							where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0 
							and inte_task.is_delete=0 and inte_task_case.is_delete=0 
							and sys_user_info.username=%s and inte_task_case.id=%s"""

# 修改接口状态权限校验
CHEKE_API_PERMISSION = """select inte_interface.id from sys_user_permission
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            left join sys_subsystem on sys_subsystem.project_id=sys_user_permission.project_id
                            left join inte_interface on inte_interface.subsystem_id=sys_subsystem.id
                            where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0 
                            and sys_subsystem.is_delete=0 and inte_interface.is_delete=0
                            and sys_user_info.username=%s and inte_interface.id=%s"""

# 删除环境权限校验
DELETE_ENV_PERMISSION = """select sys_env.id from sys_user_permission
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            left join sys_env on sys_env.project_id=sys_user_permission.project_id
                            where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0
                            and sys_env.is_delete=0 and sys_user_info.username='%s' 
                            and sys_env.id in (%s) ORDER BY FIND_IN_SET(sys_env.id,'%s')"""

# 删除接口权限校验
DELETE_API_PERMISSION = """select inte_interface.id from sys_user_permission
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            left join sys_subsystem on sys_subsystem.project_id=sys_user_permission.project_id
                            left join inte_interface on inte_interface.subsystem_id=sys_subsystem.id
                            where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0
                            and sys_subsystem.is_delete=0 and inte_interface.is_delete=0
                            and sys_user_info.username='%s' and inte_interface.id in (%s) ORDER BY FIND_IN_SET(inte_interface.id,'%s')"""

# 删除用例接口权限校验
DELETE_CASE_PERMISSION = """select inte_case.id from sys_user_permission
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            left join sys_subsystem on sys_subsystem.project_id=sys_user_permission.project_id
                            left join sys_module on sys_module.subsystem_id=sys_subsystem.id
                            left join inte_case on inte_case.module_id=sys_module.id
                            where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0
                            and sys_subsystem.is_delete=0 and sys_module.is_delete=0
                            and inte_case.is_delete=0 and sys_user_info.username='%s'
                            and inte_case.id in (%s) ORDER BY FIND_IN_SET(inte_case.id,'%s')"""

# 数据库工具环境删除权限校验
DELETE_DB_ENV_PERMISSION = """select sys_db_env.id from sys_user_permission
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            left join sys_db_env on sys_db_env.project_id=sys_user_permission.project_id
                            where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0
                            and sys_db_env.is_delete=0 and sys_user_info.username='%s' and 
                            sys_db_env.id in (%s) ORDER BY FIND_IN_SET(sys_db_env.id,'%s')"""

# 数据库工具sql语句删除权限校验
DELETE_DB_SQL_PERMISSION = """select sys_db_sqldetail.id from sys_user_permission
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            left join sys_db_env on sys_db_env.project_id=sys_user_permission.project_id
                            left join sys_db_sqldetail on sys_db_sqldetail.env_id=sys_db_env.id
                            where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0
                            and sys_db_env.is_delete=0 and sys_db_sqldetail.is_delete=0 and sys_user_info.username='%s'
                            and sys_db_sqldetail.id in (%s) ORDER BY FIND_IN_SET(sys_db_sqldetail.id,'%s')"""

# 报告删除权限校验
DELETE_REPORT_PERMISSION = """select inte_report.id from inte_report
                            left join inte_task on inte_report.task_id=inte_task.id
                            left join sys_user_permission on sys_user_permission.project_id=inte_task.project_id
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            where sys_user_permission.is_delete=0 and inte_task.is_delete=0 and inte_report.is_delete=0
                            and sys_user_info.is_delete=0 and sys_user_info.username='%s' 
                            and inte_report.id in (%s) ORDER BY FIND_IN_SET(inte_report.id,'%s')"""

# 任务删除权限校验
DELETE_TASK_PERMISSION = """select inte_task.id from sys_user_permission
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            left join inte_task on inte_task.project_id=sys_user_permission.project_id
                            where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0
                            and inte_task.is_delete=0 and sys_user_info.username='%s' and 
                            inte_task.id in (%s) ORDER BY FIND_IN_SET(inte_task.id,'%s')"""

# 任务接口删除
DELETE_TASK_CASE_PERMISSION = """select inte_task_case.id from sys_user_permission
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            left join inte_task on inte_task.project_id=sys_user_permission.project_id
                            left join inte_task_case on inte_task_case.task_id=inte_task.id
                            where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0
                            and inte_task_case.is_delete=0 and inte_task_case.is_delete=0
                            and sys_user_info.username='%s' and 
                            inte_task_case.id in (%s) ORDER BY FIND_IN_SET(inte_task_case.id,'%s')"""

# 参数删除权限校验
DELETE_PARAM_PERMISSION = """select sys_public_param.id from sys_user_permission
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            left join sys_public_param on sys_public_param.project_id=sys_user_permission.project_id
                            where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0 
                            and sys_user_info.username='%s' and sys_public_param.id in (%s) 
                            ORDER BY FIND_IN_SET(sys_public_param.id,'%s')"""

# 子系统删除权限校验
DELETE_SUBSYSTEM_PERMISSION = """select sys_subsystem.id from sys_user_permission
                            left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                            left join sys_subsystem on sys_subsystem.project_id=sys_user_permission.project_id
                            where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0
                            and sys_user_info.username='%s' and 
                            sys_subsystem.id in (%s) ORDER BY FIND_IN_SET(sys_subsystem.id,'%s')"""

# 模块删除权限校验
DELETE_MODULE_PERMISSION = """select sys_module.id from sys_user_permission
                        left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                        left join sys_subsystem on sys_subsystem.project_id=sys_user_permission.project_id
                        left join sys_module on sys_module.subsystem_id=sys_subsystem.id
                        where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0
                        and sys_subsystem.is_delete=0 and sys_user_info.username='%s' and 
                        sys_module.id in (%s) ORDER BY FIND_IN_SET(sys_module.id,'%s')"""

# 删除加密权限校验
DELETE_ENCRYPTION_PERMISSION = """select sys_encryption.id from sys_user_permission
                        left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                        left join sys_encryption on sys_encryption.project_id=sys_user_permission.project_id
                        where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0 and sys_encryption.is_delete=0 
                        and sys_user_info.username='%s' and sys_encryption.id in (%s) 
                        GROUP BY FIND_IN_SET(sys_encryption.id,'%s')"""

# 数据驱动删除权限校验
EDLETE_DATADRIVEN_PERMISSION = """select sys_data_driven.id from sys_user_permission
                        left join sys_user_info on sys_user_permission.user_id=sys_user_info.id
                        left join sys_data_driven on sys_data_driven.project_id=sys_user_permission.project_id
                        where sys_user_permission.is_delete=0 and sys_user_info.is_delete=0 and sys_data_driven.is_delete=0 
                        and sys_user_info.username='%s' and sys_data_driven.id in (%s) 
                        ORDER BY FIND_IN_SET(sys_data_driven.id,'%s')"""

# 导出任务接口数据到excel
TASK_CASE_INTERFACE_DATA = """select  inte_interface.interface_name, inte_interface.req_path, 
                        case when interface_case_count  then interface_case_count else 0 end, inte_interface.id 
                        from inte_interface left join 
                        (select inte_interface.id inte_id, sum(case when inte_interface.id  then 1 else 0 end) 
                        interface_case_count  from inte_task 
                        left join inte_task_case on inte_task.id=inte_task_case.task_id 
                        left join inte_case on inte_task_case.case_id=inte_case.id 
                        left join inte_interface on inte_case.interface_id=inte_interface.id 
                        where inte_task_case.is_delete=0 and inte_task_case.state=1 
                        and inte_case.is_delete=0 and inte_case.state=1
                        and inte_interface.is_delete=0 and inte_interface.state=1
                        and inte_case.case_type=1 and inte_task.id=%s group by inte_interface.id) 
                        a on inte_interface.id=a.inte_id where subsystem_id in (%s) and inte_interface.is_delete=0 
                        and inte_interface.state=1 ORDER BY interface_case_count desc"""

# TODO 定制查询报告接口
SELECT_REPORT = """select report_path,inte_report.`job_status`,inte_report.`job_count` from inte_report
                left join inte_task on inte_report.task_id=inte_task.id
                left join sys_user_permission on sys_user_permission.project_id=inte_task.project_id
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                WHERE inte_report.id =%s and sys_user_info.username='%s'"""

# TODO 校验是否被任务勾选
SELECT_CASE_TO_TASK = """select case_id from inte_task_case where is_delete=0 and 
        case_id in (%s) ORDER BY FIND_IN_SET(case_id,'%s')"""

# TODO 查询提取变量字段
SELECT_TASK_EXTRACT_LIST = """select extract_list from inte_task_case where is_delete=0 and task_id in (%s) 
                        ORDER BY FIND_IN_SET(task_id,'%s')"""

SELECT_CASE_EXTRACT_LIST = """select extract_list from inte_case  where is_delete=0 and extract_list like '%%%s%%'"""

# TODO 查询用户操作日志
SELECT_OPERATE = """ select DATE_FORMAT(a.operate_time,'%%Y-%%m-%%d %%H:%%i:%%S'),sys_user_info.username_cn,
            b.dict_value,c.dict_value,a.object_desc from sys_user_operate a 
            left join sys_user_info on sys_user_info.username=a.username
            left join (select id,dict_key,dict_value from sys_dict where dict_type=2 order by id) b on a.behavior=b.dict_key 
            left join (select id,dict_key,dict_value from sys_dict where dict_type=3 order by id) c on a.object_name=c.dict_key 
            where case when '%s' and '%s' then a.operate_time  between '%s' and '%s' else 1 end and 
            case when ''='%s' then 1 else a.behavior='%s'  end and sys_user_info.username_cn like '%%%s%%' order by a.operate_time desc
            limit %s,%s"""
SELECT_OPERATE_TYPE = """select id, dict_key, dict_value from `sys_dict` where dict_type=2"""
# 查询日志条数
COUNT_OPERATE = """select count(*) from sys_user_operate a
            left join sys_user_info on sys_user_info.username=a.username
            left join (select id,dict_key,dict_value from sys_dict where dict_type=2 order by id) b on a.behavior=b.dict_key 
            left join (select id,dict_key,dict_value from sys_dict where dict_type=3 order by id) c on a.object_name=c.dict_key 
            where case when '%s' and '%s' then a.operate_time  between '%s' and '%s' else 1 end and 
            case when ''='%s' then 1 else a.behavior='%s'  end and sys_user_info.username_cn like '%%%s%%'"""