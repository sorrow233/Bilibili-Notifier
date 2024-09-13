import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from datetime import datetime

# 全局任务列表
task_list = []

class BilibiliNotifier:
    def __init__(self, notify_mode, up_id, target_text=None, sender_email="", receiver_email="", password="", smtp_server='smtp.gmail.com',
                 smtp_port=587):
        self.notify_mode = notify_mode  # 通知模式：1为关键词匹配，2为自动检测新视频
        self.up_id = up_id  # 保存UP主ID
        self.target_text = target_text  # 目标关键词，只有在模式1时才需要
        self.sender_email = sender_email
        self.receiver_email = receiver_email
        self.password = password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.up_username = None  # 用于存储UP主用户名
        self.last_video_ids = []  # 用于存储上一次检测时的视频ID列表

    def get_webpage_content(self, url):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 启用无头模式
        chrome_options.add_argument("--disable-gpu")  # 禁用 GPU 渲染
        chrome_options.add_argument("--no-sandbox")  # 避免 root 权限问题
        chrome_options.add_argument("--disable-dev-shm-usage")  # 解决共享内存问题
        chrome_options.add_argument("--window-size=1920x1080")  # 设置窗口大小

        # 模拟真实浏览器的 User-Agent
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        # 禁用自动化控制标志
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)


        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)

        time.sleep(5)  # 等待页面加载
        html_content = driver.page_source
        driver.quit()

        return html_content

    def parse_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')

        # 查找UP主用户名，位于<span id="h-name">标签中
        self.up_username = soup.find('span', {'id': 'h-name'}).text.strip()

        # 获取所有视频的标题和链接，返回格式：[{"title": ..., "id": ...}, ...]
        video_elements = soup.find_all('a', class_='title')
        video_data = []
        for video in video_elements:
            title = video['title']
            href = video['href']
            video_id = href.split('/')[-1]  # 从URL中提取视频ID
            video_data.append({'title': title, 'id': video_id})
        return video_data

    def check_for_update(self, video_data):
        # 如果选择的是关键词匹配模式
        if self.notify_mode == 1:
            for video in video_data:
                if self.target_text in video['title']:
                    return True
            return False
        # 如果选择的是自动检测新视频模式
        elif self.notify_mode == 2:
            current_video_ids = [video['id'] for video in video_data]
            if not self.last_video_ids:
                # 如果是第一次检测，初始化视频ID列表，不发送通知
                self.last_video_ids = current_video_ids
                return False
            # 比较新旧视频ID列表，判断是否有新视频
            new_videos = set(current_video_ids) - set(self.last_video_ids)
            if new_videos:
                # 如果有新视频，更新ID列表并返回True
                self.last_video_ids = current_video_ids
                return True
            return False

    def send_email_notification(self, video_data=None):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n脚本运行时间: {current_time}")

        subject = "B站更新提醒"
        body = ""
        if self.notify_mode == 1:
            body = f"检测到B站UP主 <b>{self.up_username}</b> 发布了新的内容：{self.target_text}"
        elif self.notify_mode == 2:
            new_videos = [video for video in video_data if video['id'] not in self.last_video_ids]
            body = f"检测到B站UP主 <b>{self.up_username}</b> 发布了新的视频：\n"
            for video in new_videos:
                body += f"<b>{video['title']}</b>，链接：<a href='https://www.bilibili.com/video/{video['id']}'>点击查看</a><br>"

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, self.receiver_email, msg.as_string())
            server.quit()
            print("提醒邮件已发送")
            return True
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False

    def run(self, url):
        while True:
            html_content = self.get_webpage_content(url)
            video_data = self.parse_html(html_content)

            if self.check_for_update(video_data):
                if self.send_email_notification(video_data):
                    print(f"{self.up_username}更新提醒已发送，任务结束")
                    break  # 邮件发送成功后终止任务
            else:
                print("未检测到目标内容，30分钟后再次检测...")
            time.sleep(1800)


def print_running_tasks():
    """
    打印当前所有正在运行的任务，并显示线程信息
    """
    print("\n当前后台运行的任务列表：")
    for idx, task in enumerate(task_list, 1):
        task_type = "关键词任务" if task['notify_mode'] == 1 else "UP主更新提醒"
        task_info = task['target_text'] if task['notify_mode'] == 1 else f"UP主ID: {task['up_id']}"
        thread_id = task['thread_id']  # 打印线程ID
        print(f"{idx:02d}【{task_type}】：{task_info} (线程ID: {thread_id})")

    # 打印当前活跃线程数
    print(f"\n当前活跃线程数: {threading.active_count()}\n")


def start_notifier(up_id, notify_mode, target_text=None):
    sender_email = "k.onband.fan@gmail.com"
    receiver_email = "receiver_email"
    password = "hpaj otpg igpr ynuo"

    notifier = BilibiliNotifier(notify_mode, up_id, target_text, sender_email, receiver_email, password)

    url = f'https://space.bilibili.com/{up_id}'
    notifier.run(url)


if __name__ == "__main__":
    while True:
        up_id = input("请输入UP主ID: ")
        print("请选择提醒方式: 1 - 关键词匹配，2 - 自动检测新视频")
        notify_mode = int(input("输入提醒方式(1或2): "))

        target_text = None
        if notify_mode == 1:
            target_text = input("请输入要抓取的关键词: ")

        # 为每个任务创建一个新的线程
        task_thread = threading.Thread(target=start_notifier, args=(up_id, notify_mode, target_text))
        task_thread.daemon = True
        task_thread.start()

        # 添加任务到全局任务列表，并记录线程ID
        task_list.append({
            'notify_mode': notify_mode,
            'up_id': up_id,
            'target_text': target_text,
            'thread_id': task_thread.ident  # 保存线程ID
        })

        print(f"任务已添加到后台，您可以继续输入新的任务。")

        # 打印当前所有运行的任务
        print_running_tasks()
