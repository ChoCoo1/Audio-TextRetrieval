import os
import requests
import subprocess
import time
import csv
from tqdm import tqdm  # 用于显示进度条
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


class NewsScraper:
    def __init__(self, base_url, data_folder='Data'):
        self.base_url = base_url
        self.data_folder = data_folder
        self.setup_selenium()

    def setup_selenium(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images
        chrome_options.add_argument("--disable-extensions")  # Disable browser extensions
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def visit_page(self):
        self.driver.get(self.base_url)
        time.sleep(1)

    def select_date(self, year, month, day):
        date_script = f"Module.calendarArray[0].calendar_day_click('{year}-{month}-{day}');"
        self.driver.execute_script(date_script)
        # 等待1秒
        time.sleep(1)

    def get_news_links(self):
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        return soup.select('ul.rililist li')[1:]  # 跳过第一个新闻条目

    def download_video_audio(self, video_url, audio_filename):
        # 禁用详细的错误日志并隐藏横幅信息
        ffmpeg_command = ['ffmpeg', '-hwaccel' ,'videotoolbox','-i', video_url, '-vn', '-acodec', 'mp3','-threads','32','-loglevel', 'quiet', '-nostats', audio_filename]
        subprocess.run(ffmpeg_command)

    def save_to_csv(self, csv_file, data):
        # 每次爬取一个新闻时，将其追加到 CSV 文件中
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['日期', '音频文件', '新闻标题', '新闻内容'])
            writer.writerows(data)

    def scrape_news(self, year, month, day):
        # 获取新闻链接
        li_tags = self.get_news_links()
        csv_file = os.path.join(self.data_folder, "news_data.csv")

        for idx, li in enumerate(tqdm(li_tags, desc=f"下载 {year}-{month:02d}-{day:02d}", unit="news")):
            link_tag = li.find('a', href=True)
            if link_tag:
                href = link_tag['href']
                title = link_tag.get('title', '').replace('[视频]', '').strip()
                if not href.startswith('http'):
                    href = "https:" + href

                # 打开新闻链接
                self.driver.get(href)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                )
                new_soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                # 简化音频文件名，添加日期和新闻序号
                audio_filename = os.path.join(self.data_folder, f"{year}_{month:02d}_{day:02d}_news_{idx + 1}.mp3")

                # 下载视频音频
                video_tag = new_soup.find('video')
                if video_tag:
                    source_tag = video_tag.find('source')
                    if source_tag and source_tag['src']:
                        self.download_video_audio(source_tag['src'], audio_filename)

                # 提取新闻文本内容
                content_div = new_soup.find('div', id='content_area')
                text_content = ''
                if content_div:
                    paragraphs = content_div.find_all('p')
                    text_content = '\n'.join([p.get_text(strip=True) for p in paragraphs])
                    text_content = text_content.lstrip("央视网消息（新闻联播）：")

                # 将数据保存到 CSV 行
                csv_data = [[f"{year}-{month:02d}-{day:02d}", f"{year}_{month:02d}_{day:02d}_news_{idx + 1}.mp3", title, text_content]]
                self.save_to_csv(csv_file, csv_data)

    def close(self):
        self.driver.quit()


# 使用示例
from datetime import datetime, timedelta

if __name__ == "__main__":
    scraper = NewsScraper('https://tv.cctv.com/lm/xwlb/index.shtml')

    # 设置开始和结束日期
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 8, 22)

    # 用 timedelta 遍历日期
    current_date = start_date
    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        day = current_date.day

        # 访问页面
        scraper.visit_page()

        # 选择日期
        scraper.select_date(year, month, day)

        # 抓取并保存新闻
        scraper.scrape_news(year, month, day)

        # 增加一天
        current_date += timedelta(days=1)

    # 完成后关闭浏览器
    scraper.close()
