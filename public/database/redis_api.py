#!/usr/bin/python
# -*- coding:utf-8 -*-

from redis import Redis, ConnectionPool


# from client import Redis
# from connection import ConnectionPool

class RedisObj(object):
    """
    普通的数据直接传输
    多数据用管道
    """

    def __init__(self, host='127.0.0.1', port=6379, db=1, password='123456'):
        if not hasattr(RedisObj, 'pool'):
            RedisObj.create_pool(host, port, db, password)
        self._connection = Redis(connection_pool=RedisObj.pool)

    def connect_test(self, host, port, password):
        try:
            result = Redis(host=host, port=port, password=password).ping()
        except:
            result = {"msg": "error"}
        return result

    def __setitem__(self, key, value):
        if type(key) == dict:  # 设置多值
            pi = self._connection.pipeline()
            pi.mget(value)
            return pi.execute()
        try:
            return self._connection.set(key, value)
        except Exception as e:
            return e.message

    def __getitem__(self, item):
        if type(item) == list:
            pi = self._connection.pipeline()
            # for each in item:
            pi.mget(item)
            return pi.execute()
        try:
            return self._connection.get(item)
        except Exception as e:
            return e.message

    @staticmethod
    def create_pool(host, port, db, password):
        RedisObj.pool = ConnectionPool(host=host, port=port, db=db, password=password)

    # 单个键、值设置
    def set_data(self, key='', value=''):
        if not key:
            return False
        try:
            return self._connection.set(key, value)
        except Exception as e:
            return e.message

    # 批量设置
    def mset_data(self, data_dict):
        if not data_dict:
            return False
        try:
            pi = self._connection.pipeline()
            pi.mset(data_dict)
            return pi.execute()
        except Exception as e:
            return e.message

    # 获取键值
    def get_data(self, key):
        try:
            datas = self._connection.get(key)
            self._connection.connection_pool.disconnect()
            # print('key: ' + str(key))
            # print('datas: ' + str(datas))
            if datas:
                return str(datas, encoding="utf-8")
            return datas
        except Exception as e:
            return e.message

    # 批量获取数据
    def mget_data(self, keys):
        try:
            pi = self._connection.pipeline()
            pi.mget(keys)
            datas = pi.execute()
            if len(datas) > 0:
                datas = datas[0]
                ret_datas = []
                for data in datas:
                    if data:
                        ret_datas.append(eval(data))
                return ret_datas
            else:
                return []
        except Exception as e:
            return e.message

    # 模糊查询key
    def get_keys(self, key):
        try:
            return self._connection.keys(key)
        except:
            return []

    def del_data(self, key):
        """
        delete cache by key
        """
        try:
            return self._connection.delete(key)
        except Exception as e:
            return e.message

    # 从左往右插入队列
    def lpush(self, key, values):
        if not key:
            return False
        try:
            return self._connection.lpush(key, values)
        except Exception as e:
            return e.message

    # 从右往左插入队列
    def rpush(self, key, values):
        if not key:
            return False
        try:
            return self._connection.rpush(key, values)
        except Exception as e:
            return e.message

    # 队列取值
    def lrange(self, key, start, end):
        if not key:
            return False
        try:
            return self._connection.lrange(key, start, end)
        except Exception as e:
            return e.message

    # 删除队列最左边第一条
    def lpop(self, key):
        if not key:
            return False
        try:
            return self._connection.lpop(key)
        except Exception as e:
            return e.message

    # 删除队列最右边第一条
    def rpop(self, key):
        if not key:
            return False
        try:
            return self._connection.rpop(key)
        except Exception as e:
            return e.message


if __name__ == '__main__':
    rs = RedisObj()
    # rs.lpush(key, {"dev_sn": "1234567890", "cardno": "1"})
    # rs.lpush(key, {"dev_sn": "1234567890", "cardno": "2"})
    # rs.lpush(key, {"dev_sn": "1234567890", "cardno": "3"})
    #
    # rs.rpush(key, {"dev_sn": "1234567890", "cardno": "4"})
    # rs.rpush(key, {"dev_sn": "1234567890", "cardno": "5"})
    #
    # print rs.lrange(key, 0, 10)
    #
    # rs.lpop(key)
    #
    # print rs.lrange(key, 0, 10)

    # #     # while 1:
    # #     #     for i in range(100):
    # #     # rs = RedisObj(host='127.0.0.1', port=65433, db=1)
    #     rs = RedisObj()
    #     rs.set_data("333", "22343")
    #     rs.mset_data({"3344": {"33": 33, "44": 44}, "1122": {"11": 11, "22": 22}})
    #     print rs.set_data('test', 'test1')
    #     print rs.get_data('test')
    #     rs.del_data("dmserver:V4112620785:info")
    print(rs.get_keys("*"))
    print(rs.get_data("mykey"))
    # print(rs.get_data("dmserver:2014403622:info"))
    # print(rs.get_data("dmserver:004A770124011F13:info"))
    # print(rs.get_data("dmserver:2014403622:004A770124011F13:info"))
    # # print rs.set_data("dmserver:V4112620785:info", {'door': 2, 'last_active': 0, 'online_status': 'online', 'battery': '', 'lock': 1, 'devSn': 'V4112620785', 'dev_sn': 'V4112620785', 'dev_type': 0, 'alarm': 0, 'version_code': 0, 'version': '101', 'comm_type': 'TCP'})
    # # rs._connection.delete(*rs._connection.keys(pattern='*'))
    # print(rs.del_data("devices:2014403622:info"))
    print(RedisObj().get_data("mykey"))
