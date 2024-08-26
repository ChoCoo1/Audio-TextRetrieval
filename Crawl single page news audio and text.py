# 引用模块
import requests
import subprocess
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# 目标URL：CCTV主页
url = 'https://tv.cctv.com/lm/xwlb/index.shtml'

# 获取网页内容
response = requests.get(url)
response.encoding = 'utf-8'  # 设置编码方式
html_content = response.text

# 解析HTML
soup = BeautifulSoup(html_content, 'html.parser') # soup解析了当前页面的内容

# 选择该新闻总览页面，读取每一个子新闻
li_tags = soup.select('ul.rililist li') # 获取所有包含在<li>标签内的<a>标签

# 设置 Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# 创建 WebDriver 实例
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 跳过第一个 <li> 元素（因为第一个是全集，我们只需要爬取每一个子新闻）
for li in li_tags[1:]:
    link_tag = li.find('a', href=True)
    if link_tag:
        href = link_tag['href']  # 获取链接
        title = link_tag.get('title', '')  # 获取标题
        title = title.replace('【视频】', '')  # 去掉【视频】二字
        print(f"链接: {href}")
        print(f"标题: {title}")

        if not href.startswith('http'):
            href = "https:" + href

        # 使用 Selenium 打开该链接
        driver.get(href)

        # 等待页面加载完成
        time.sleep(5)

        # 获取页面源代码
        page_content = driver.page_source

        # 使用 BeautifulSoup 解析该页面
        new_soup = BeautifulSoup(page_content, 'html.parser')

        # 查找 <video> 标签中的 <source> 元素
        video_tag = new_soup.find('video')
        if video_tag:
            source_tag = video_tag.find('source')
            if source_tag:
                src = source_tag.get('src')
                if src:
                    print(f"视频流链接: {src}")

                    # 根据标题命名MP3文件
                    mp3_file = f'{title}.mp3'

                    # 使用 ffmpeg 下载视频流并直接转换为 MP3
                    ffmpeg_command = [
                        'ffmpeg',
                        '-i', src,  # 输入流
                        '-vn',  # 不处理视频流
                        '-acodec', 'mp3',  # 音频编码格式
                        '-loglevel', 'error',  # 只显示错误信息
                        mp3_file  # 输出 MP3 文件
                    ]

                    # 执行 ffmpeg 命令
                    subprocess.run(ffmpeg_command)

                    print(f"音频已保存为 {mp3_file}")

        # 提取文本内容
        content_div = new_soup.find('div', id='content_area')
        if content_div:
            paragraphs = content_div.find_all('p')
            text_content = '\n'.join([p.get_text(strip=True) for p in paragraphs])

            # 去除开头的特定文字
            text_content = text_content.lstrip("央视网消息（新闻联播）：")

            # 根据标题命名TXT文件
            txt_file = f'{title}.txt'
            with open(txt_file, 'w', encoding='utf-8') as file:
                file.write(text_content)

            print(f"文本内容已保存为 {txt_file}")

# 关闭 WebDriver
driver.quit()
