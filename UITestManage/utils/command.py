import os
import platform
from public.thread_manage import *


class Command:
    """
    操作系统命令
    """
    JAR_PATH = r'E:\test\www'
    if platform.system().lower() == 'windows':
        RUN_SERVER = 'java -jar selenium-server-standalone-3.141.0.jar -role hub'
    else:
        pass

    @classmethod
    def get_cmd_result(cls, com: str) -> list:
        result_list = []
        result = os.popen(com).readlines()
        for i in result:
            if i == '\n':
                continue
            result_list.append(i.strip('\n'))
        return result_list

    @classmethod
    def exec_cmd(cls, com: str):
        os.system(com)

    @classmethod
    def start_server(cls, ip=None, port=None, role_type='hub'):
        global_thread_pool.lock.acquire()
        try:
            if role_type == 'hub':
                command = 'netstat -ano | findstr 4444'
                result = cls().get_cmd_result(command)
                if len(result) > 0:
                    kill_command = f'taskkill /pid {result[0][-5:]} -t -f'
                    cls().exec_cmd(kill_command)
                os.chdir('E:\\test\\www')
                cls().exec_cmd(cls.RUN_SERVER)
            else:
                command = f'Java -jar selenium-server-standalone-3.141.0.jar -role node -host {ip} -port {port} -hub http://10.8.72.59:4444/grid/register'
                os.chdir('E:\\test\\www')
                cls().exec_cmd(command)
            global_thread_pool.lock.release()
        except Exception as e:
            print(e)
            trace_log = traceback.format_exc()
            logger.error('异步任务执行失败:\n %s' % trace_log)
            global_thread_pool.lock.release()


if __name__ == "__main__":
    print(Command.start_server(4444))
