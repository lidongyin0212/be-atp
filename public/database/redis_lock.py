
import datetime
import redis
from contextlib import contextmanager
from .redis_api import RedisObj

@contextmanager
def redislock(name, timeout=(24 + 2) * 60 * 60):
    try:
        today_string = datetime.datetime.now().strftime("%Y-%m-%d")
        key = f"servername.lock.{name}.{today_string}"
        # log.info(f"<Redis Lock> {key}")
        # 原子性的锁: 不存在，创建锁，返回1，相当于获取锁；存在，创建锁失败，返回0，相当于获取锁失败；过一段时间超时，避免死锁
        # nx: 不存在，key值设置为value，返回1，存在，不操作，返回0
        # ex: 设置超时
        lock = RedisObj().set_data(key, value=1) #set(key, value=1, nx=True, ex=timeout)
        yield lock
    finally:
        RedisObj().del_data(key) # 释放锁

# 要被执行的任务函数
def tick():
    with redislock() as lock:
        if lock:
            print('Tick! The time is: %s' % datetime.now())