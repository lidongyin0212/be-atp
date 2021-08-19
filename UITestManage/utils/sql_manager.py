# 用例树形图

CASE_TREE = """select c.id, c.case_name
                from `ui_case` c
                left join sys_subsystem on sys_subsystem.id=c.subsystem_id
                left join sys_project on sys_project.id=sys_subsystem.project_id
                left join sys_user_permission on sys_user_permission.project_id=sys_project.id
                left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                where c.is_delete=0 and sys_user_permission.is_delete=0 and
                sys_project.is_delete=0 and sys_user_info.is_delete=0 and sys_user_info.username='%s' 
                and sys_subsystem.id=%s order by c.create_time"""
# 用例列表
CASE_LIST_LIKE = """select c.id, c.case_name, c.case_desc, c.subsystem_id, p.project_name, c.step_list, 
                    c.username, DATE_FORMAT(c.update_time, '%%Y-%%m-%%d %%H:%%i:%%S') 
                    from ui_case c 
                    left join sys_subsystem on sys_subsystem.id=c.subsystem_id
                    left join sys_project as p on sys_subsystem.project_id = p.id 
                    left join sys_user_permission on sys_user_permission.project_id=p.id
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    where sys_user_permission.is_delete=0 and c.is_delete=0 and p.is_delete=0
                    and sys_user_info.username='%s' and c.case_name like '%%%s%%' 
                    and sys_subsystem.id=%s
                    order by c.create_time"""

# TODO 用例报告
CASE_REPORT_LIST = """select ui_report.id, case_name, CASE WHEN report_type=1 THEN '用例' END r_type, report_path,
         file_name, DATE_FORMAT(ui_report.update_time, '%%Y-%%m-%%d %%H:%%i:%%S'), 
         ui_report.username from `ui_report` left join `ui_case` on `ui_case`.id=`ui_report`.ui_case_id where ui_report.is_delete=0 and 
         ui_case.id=%s ORDER BY ui_report.update_time desc"""

# 指定用例信息
SELECT_CASE_INFO = """select `ui_case`.id, `ui_case`.case_name, case_desc,
                    `ui_case`.subsystem_id,step_list  from `ui_case`
                    left join sys_subsystem on sys_subsystem.id=`ui_case`.subsystem_id
                    left join sys_project on sys_project.id=sys_subsystem.project_id
                    left join sys_user_permission on sys_user_permission.project_id=`sys_project`.id
                    left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                    where sys_user_info.username=%s and `ui_case`.id=%s and sys_user_permission.is_delete=0
                    and `ui_case`.is_delete=0"""

# 个人项目权限
GET_PERSON_PROJECT = """select project_id from sys_user_permission 
                        left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                        where sys_user_info.username=%s and project_id=%s and sys_user_permission.is_delete=0"""

# 个人项目权限
GET_PERSON_SUBSYSTEM = """select sys_subsystem.id from sys_subsystem
                        left join sys_project on sys_project.id=sys_subsystem.project_id
                        left join sys_user_permission on sys_project.id=sys_user_permission.project_id
                        left join sys_user_info on sys_user_info.id=sys_user_permission.user_id
                        where sys_user_info.username=%s and sys_subsystem.id=%s and sys_user_permission.is_delete=0"""
