"""一些生成器方法，生成随机数，手机号，以及连续数字等"""
import random
from faker import Factory
from .mysqldb import *
import datetime
import time

fake = Factory().create('zh_CN')


def random_phone_number(*arg):
    """生成随机手机号码"""
    return fake.phone_number()


def random_name(*arg):
    """生成随机姓名"""
    return fake.name()


def random_ssn(*arg):
    """生成随机身份证号(18位)"""
    return fake.ssn()


def random_address(*arg):
    """生成随机地址"""
    return fake.address()


def random_email(*arg):
    """生成随机email"""
    return fake.email()


def random_ipv4(*arg):
    """生成随机IPV4地址"""
    return fake.ipv4()


def random_postcode(*arg):
    """生成随机邮编"""
    return fake.postcode()


def random_mac(*arg):
    """生成随机MAC地址"""
    return fake.mac_address()


def random_username(*arg):
    """生成随机用户名"""
    return fake.user_name()


def random_useragent(*arg):
    """生成随机user_agent信息"""
    return fake.user_agent()


def random_date(*arg):
    """生成随机日期"""
    return fake.date()


def random_time(*arg):
    """生成随机时间（1970年1月1日至今）"""
    return fake.date_time().strftime('%Y-%m-%d %H:%M:%S')


def random_unixtime(*arg):
    """生成随机unix时间（时间戳）,需要填一个时间戳长度"""
    return fake.unix_time()


def random_job(*arg):
    """生成随机工作职位"""
    return fake.job()


def random_text(*arg):
    """生成随机生成一篇文章，需要填一个最大长度的参数"""
    return fake.text(max_nb_chars=int(arg[0][0]))


def random_str(*arg):
    """长度在最大值与最小值之间的随机字符串，需要填最大和最小值，用英文逗号隔开
        例如：参数填写1，9，即生成1-9之间随机长度的字符串"""
    return fake.pystr(min_chars=int(arg[0][0]), max_chars=int(arg[0][1]))


def factory_generate_ids(id=0, *arg):
    """ 生成一个递增数字，需要填两个参数初始值和步长，用英文逗号隔开
        例如：参数填写1，5，即每次生成一个从1开始，每次加5的数字 """

    val = int(arg[0][0]) + int(arg[0][1])
    alter_param = str(val) + ',' + str(arg[0][1])
    sql = """UPDATE `sys_public_param` SET `input_params` = '%s' WHERE `id` = '%s'""" % (
        str(alter_param),
        str(id),
    )
    MySQLHelper().update(sql)
    return str(val)


def factory_generate_ids_test(*arg):
    """ 生成一个递增数字，需要填两个参数初始值和步长，用英文逗号隔开
        例如：参数填写1，5，即每次生成一个从1开始，每次加5的数字 """
    val = int(arg[0][0]) + int(arg[0][1])
    return val


def factory_choice_generator(values):
    """ 从列表中随机选择一个值返回，需要填一个列表
        例：参数填入aaaa,555,哈哈哈，999，每次从这个列表里随机选一个值输出 """

    my_list = list(values)
    rand = random.Random()
    val = rand.choice(my_list)
    return val


def get_now_time(*arg):
    """获取当前时间，输入参数格式：%Y-%m-%d %H:%M:%S，输出格式如下：2020-02-29 08:30:00"""
    now_time = datetime.datetime.now().strftime(*arg[0])
    return now_time


def get_now_timestamp(*arg):
    """获取当前时间的时间戳，需要填一个时间戳长度"""
    digits = int(arg[0][0])
    time_stamp = time.time()
    digits = 10 ** (digits - 10)
    time_stamp = int(round(time_stamp * digits))
    return str(time_stamp)


if __name__ == '__main__':
    print(random_phone_number())
    print(random_name())
    print(random_address())
    print(random_email())
    print(random_ssn())
    print(random_str(min_chars=6, max_chars=8))
    id_gen = factory_generate_ids(starting_id=0, increment=2)()
    for i in range(5):
        print(next(id_gen))

    choices = ['John', 'Sam', 'Lily', 'Rose']
    choice_gen = factory_choice_generator(choices)()
    for i in range(5):
        print(next(choice_gen))
