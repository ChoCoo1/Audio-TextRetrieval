# 引用模块
import requests
from bs4 import BeautifulSoup
import time

# 目标URL：CCTV主页
url = 'https://tv.cctv.com/2024/01/01/VIDEI3jZW39xe1Ld2uG7qp5C240101.shtml?spm=C31267.PXDaChrrDGdt.EbD5Beq0unIQ.75'

# 获取网页内容
response = requests.get(url)
response.encoding = 'utf-8'  # 设置编码方式
html_content = response.text

# 解析HTML
soup = BeautifulSoup(html_content, 'html.parser') # soup解析了当前页面的内容
print(soup)