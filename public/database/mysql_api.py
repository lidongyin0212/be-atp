# -*- coding:utf-8 -*-
# 导入mysql库
import pymysql
import os


class MySQLObj(object):

    def __init__(self, host, port, user, password, db):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.conn, self.cursor = None, None

    def connect(self):
        # 打开数据库连接
        try:
            self.conn = pymysql.Connect(
                host=self.host,
                port=self.port,
                user=self.user,
                passwd=self.password,
                db=self.db,
                charset='utf8'
            )
            self.cursor = self.conn.cursor()
        except:
        # 获取一个游标(数据库操作的对象)
            return {"msg": "error"}


    # 关闭数据库连接
    def close(self):
        self.cursor.close()
        self.conn.close()

    # 增加
    # INSERT INTO course(c_name, c_weight) VALUES(%s, %d)
    def insert(self, sql, param=()):
        return self.__edit(sql, param)

    # 删除
    def delete(self, sql, param=()):
        return self.__edit(sql, param)

    # 修改
    def update(self, sql, param=()):
        return self.__edit(sql, param)

    # 增删改通用的代码
    def __edit(self, sql, param=()):
        count = 0
        try:
            # 连接数据库
            self.connect()
            # 执行SQL语句
            count = self.cursor.execute(sql, param)
            # 提交数据库事务处理
            self.conn.commit()
            return count, ''
        except Exception as e:
            # 如果出现错误就回滚
            print(e)
            self.conn.rollback()
            return -1, e

    # 查询所有
    def get_all(self, sql, param=()):
        result = ()  # 返回的结果是一个元组
        try:
            # 连接数据库
            self.connect()
            # 执行SQL语句
            if param:
                self.cursor.execute(sql, param)
            else:
                self.cursor.execute(sql)
            # 获取查询的内容
            result = self.cursor.fetchall()
            fields = self.cursor.description
            column_list = []  # 定义字段名的列表
            for i in fields:
                column_list.append(i[0])
            # 提交数据库事务处理
            self.conn.commit()
            return result, column_list, ""
        except Exception as e:
            # 如果出现错误就回滚
            print(e)
            self.conn.rollback()
            return -1, None, e

    # 查询一个
    def get_one(self, sql, param=()):
        result = ()  # 返回的结果是一个元组
        try:
            # 连接数据库
            self.connect()
            # 执行SQL语句
            if param:
                self.cursor.execute(sql, param)
            else:
                self.cursor.execute(sql)
            # 获取查询的内容
            result = self.cursor.fetchone()
            # 提交数据库事务处理
            self.conn.commit()
        except Exception as e:
            # 如果出现错误就回滚
            print(e)
            self.conn.rollback()
        return result

    def __del__(self):
        # 关闭数据库连接
        self.close()

if __name__ == "__main__":
    print(MySQLObj(host='10.8.214.191', port=3306, user='root', password='123456', db='interface_v03').get_all("select * from userinfo"))
