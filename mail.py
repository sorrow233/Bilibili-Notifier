import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
from datetime import datetime

# 邮箱配置信息
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"  # 发送邮箱
RECEIVER_EMAIL = "your_email@gmail.com"  # 接收邮箱
PASSWORD = "your_password"  # 邮箱密码或应用密码

# 发送邮件提醒的函数
def send_email():
    # 邮件内容
    subject = "时间管理提醒：是否存在浪费时间？"
    body = "请问您在最近的半小时内是否存在浪费时间？请回复'是'或'否'，并简要说明您做了什么。您有五分钟时间回复。"

    # 设置邮件内容
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # 连接到SMTP服务器并发送邮件
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # 开启TLS加密
            server.login(SENDER_EMAIL, PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print(f"提醒邮件已发送: {datetime.now()}")
    except Exception as e:
        print(f"邮件发送失败: {e}")

# 记录回复的函数
def log_response(response):
    # 将回复记录到本地文件中
    with open("time_waste_log.txt", "a") as file:
        file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {response}\n")
    print("回复已记录")

# 每半小时提醒一次的任务
def scheduled_reminder():
    # 设置每天8点到22点之间的提醒任务
    start_hour = 8
    end_hour = 22

    while True:
        current_hour = datetime.now().hour
        if start_hour <= current_hour < end_hour:
            send_email()
            # 等待35分钟后再检查回复，给予5分钟的回复时间
            time.sleep(1800)  # 每半小时发送一次
            # 假设收到的回复为"是 - 浏览了社交媒体"
            # 这里可以替换成实际邮件回复提取的内容
            sample_response = "是 - 浏览了社交媒体"
            log_response(sample_response)
        else:
            # 超过时间段时，进入下一个时间段
            print("不在提醒时间内")
            time.sleep(3600)

if __name__ == "__main__":
    scheduled_reminder()