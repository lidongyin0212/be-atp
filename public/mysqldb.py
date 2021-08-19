# 导入mysql库
from django.db import connection
import pymysql
import os
# 平台数据查询时使用

class MySQLHelper(object):
    # 数据库连接
    def connect(self):
        # 打开数据库连接
        try:
            self.conn = connection
            self.cursor = self.conn.cursor()
        except:
            # 获取一个游标(数据库操作的对象)
            return {"msg": "error"}

    # 关闭数据库连接

    def close(self):
        self.cursor.close()
        self.conn.close()
        self.cursor = None
        self.conn = None

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
        except Exception as e:
            # 如果出现错误就回滚
            print(e)
            self.conn.rollback()

        # 关闭数据库连接
        self.close()
        return count

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



if __name__ == "__main__":
    print(MySQLHelper().get_all("select * from user"))
