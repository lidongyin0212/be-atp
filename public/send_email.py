#!/usr/bin/python
# -*- coding: UTF-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import socket


class SendEmail(object):
    def __init__(self, to_list, file, task_name, flag=0):
        self.Email_service = 'mail.tcl.com'
        self.Email_port = 587
        self.username = "sdbgatp@tcl.com"
        self.password = "sdbg#0609"
        self.to_list = to_list
        self.file = file
        self.task_name = task_name
        self.flag = flag

    def send_email(self):
        # 第三方 SMTP 服务

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('10.0.0.1', 8080))
            ip = s.getsockname()[0]
        finally:
            s.close()

        message = MIMEMultipart()
        if self.flag != 0:
            report = "http://" + ip + "/" + self.file
        else:
            report = "http://" + ip + ":8081" + self.file
        part = MIMEText('Dear all:\n       内容为接口自动化测试报告，'
                        '此为自动发送邮件，请勿回复，谢谢！\n       %s' % report, 'plain', 'utf-8')
        message.attach(part)
        message['From'] = Header("自动化测试平台", 'utf-8')
        message['To'] = Header(''.join(self.to_list), 'utf-8')
        subject = '_任务名称【%s】- 接口测试报告' % self.task_name
        message['Subject'] = Header(subject, 'utf-8')

        # 添加附件
        # att1 = MIMEApplication(self.file)

        # att1 = MIMEText('report', 'base64', 'utf-8')
        # att1["Content-Type"] = 'application/octet-stream'
        # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
        # att1["Content-Disposition"] = 'attachment; filename="test.txt"'
        # message.attach(att1)

        # att1.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', 'report'))
        # message.attach(att1)

        try:
            service = smtplib.SMTP(host=self.Email_service, port=self.Email_port)
            # service.connect(host=self.Email_service, port=self.Email_port)
            # service.connect(self.Email_service, 25)  # 25 为 SMTP 端口号
            # service.ehlo()
            # service.starttls()
            service.login(self.username, self.password)
            service.sendmail(self.username, self.to_list, message.as_string(unixfrom=True))
            print('邮件发送成功')
            service.close()
        except Exception as e:
            print(e)
            print('报错，邮件发送失败')

if __name__ == '__main__':
    pass
    # re = "/result/test_result/interface/task/7/2021-06-10_15-32-43_task_3_result.html"
    # SendEmail(['lin65.zhang@tcl.com'], re).send_email()




