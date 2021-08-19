# coding:utf-8
import pymysql
import os
# 迁移环境时使用

class MySQLHelper(object):
    def __init__(self, host, port, user, passwd, db, charset='utf8'):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.db = db
        self.charset = charset

    # 数据库连接
    def connect(self):
        # 打开数据库连接
        self.conn = pymysql.connect(host=self.host, port=self.port, user=self.user, passwd=self.passwd, db=self.db,
                                    charset=self.charset)
        # 获取一个游标(数据库操作的对象)
        self.cursor = self.conn.cursor()

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
            if param:
                count = self.cursor.execute(sql, param)
            else:
                count = self.cursor.execute(sql)
            # 提交数据库事务处理
            id = self.conn.insert_id()
            self.conn.commit()
        except Exception as e:
            # 如果出现错误就回滚
            print(e)
            self.conn.rollback()

        # 关闭数据库连接
        self.close()
        return count, id

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
            # 提交数据库事务处理
            self.conn.commit()
        except Exception as e:
            # 如果出现错误就回滚
            print(e)
            self.conn.rollback()

        # 关闭数据库连接
        self.close()

        return result

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

        # 关闭数据库连接
        self.close()

        return result
