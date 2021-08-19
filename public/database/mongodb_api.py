# -*- coding:utf-8 -*-
# 10.8.202.167 31009
# fms_cjm fmscjm123456
import pymongo


class MongoObj:
    def __init__(self, host, port, db_name, username=None, password=None):
        self.db_name = db_name
        self.mongo_client = pymongo.MongoClient(host, port,serverSelectionTimeoutMS=10000, socketTimeoutMS=10000)
        if username and password:
            self.mongo_client[db_name].authenticate(username, password)
        self.db = self.mongo_client[db_name]

    def connect(self):
        try:
            self.mongo_client.server_info()
            return True
        except:
            return {"msg": "error"}
        finally:
            self.mongo_client.close()

    # 插入单条数据
    def insertOne(self, collection, info_dict):
        """
        :param collection: 集合名称
        :param info_dict: 插入集合字典
        :return:
        """
        try:
            coll = self.db[collection]
            if isinstance(info_dict, dict):
                return coll.insert_one(info_dict)
        except Exception as e:
            print(e)

    # 插入多条数据
    def insertMany(self, collection, info_list):
        """
        :param collection: 集合名称
        :param info_dict: 插入集合列表
        :return: 
        """
        try:
            coll = self.db[collection]
            if isinstance(info_list, list):
                return coll.insert_one(info_list)
        except Exception as e:
            print(e)

    # 删除一条数据 默认删除第一条
    def delete_one(self, collection, info_dict):
        """
        :param collection: 集合名称
        :param info_dict: 删除条件集合
        :return: 
        """
        try:
            coll = self.db[collection]
            if isinstance(info_dict, dict):
                return coll.delete_one(info_dict)
        except Exception as e:
            print(e)

    # 删除满足条件的所有数据
    def remove(self, collection, info_dict):
        """
        :param collection: 集合名称
        :param info_dict: 删除条件集合
        :return: 
        """
        try:
            coll = self.db[collection]
            if isinstance(info_dict, dict):
                return coll.delete_one(info_dict)
        except Exception as e:
            print(e)

    # 更新满足条件的第一条
    def update_one(self, collection, filter_dict, update_dict):
        """
        :param collection: 集合名称
        :param filter_dict: 过滤条件字典
        :param update_dict: 更新条件字段  更新的内容，必须用$操作符 update_one(update_condition, {'$set' : info})
        :return:
        """
        try:
            coll = self.db[collection]
            if isinstance(filter_dict, dict) and isinstance(update_dict, dict):
                return coll.update_one(filter_dict, update_dict)
        except Exception as e:
            print(e)

    # 更新满足条件的所有
    def update(self, collection, filter_dict, update_dict):
        """
        :param collection: 集合名称
        :param filter_dict: 过滤条件字典
        :param update_dict: 更新条件字段  更新的内容，必须用$操作符 update_one(update_condition, {'$set' : info})
        :return:
        """
        try:
            coll = self.db[collection]
            if isinstance(filter_dict, dict) and isinstance(update_dict, dict):
                return coll.update_many(filter_dict, update_dict)
        except Exception as e:
            print(e)

    # 查询一条数据
    def find_one(self, collection, find_condition):
        """
        :param collection: 集合名称
        :param find_condition: 查询过滤条件
        :return:
        """
        try:
            coll = self.db[collection]
            if isinstance(find_condition, dict):
                return coll.find_one(find_condition)
        except Exception as e:
            print(e)

    # 查询多条数据
    def find(self, collection, find_condition):
        """
        :param collection: 集合名称
        :param find_condition: 查询过滤条件
        :return:
        """
        try:
            coll = self.db[collection]
            if isinstance(find_condition, dict):
                return list(coll.find(find_condition))
        except Exception as e:
            print(e)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('关闭mongo数据库连接')
        self.mongo_client.close()
        self.mongo_client = None

    def hello(self):
        print('hello')


if __name__ == "__main__":
    # with MongoObj('10.8.202.167', 31009, 'fms_cjm', 'fms_cjm', 'fmscjm123456') as mongo:
    #     # some code here
    #     mongo.hello()
    print(MongoObj('10.8.202.167', 31009, 'fms_cjm', 'fms_cjm', 'fmscjm123456').connect())
