import requests
from bs4 import BeautifulSoup
import re
import json
import os

class HACGScraper:
    def __init__(self, url, filepath):
        self.url = url
        self.filepath = filepath

    def get_pages(self):
        response = requests.get(self.url)
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')
        div_ele = soup.find('div', class_='wp-pagenavi')
        page_text = div_ele.get_text() if div_ele else ''

        pages = None
        if "共" in page_text:
            pages = int(page_text.split('共')[1].split('页')[0])

        return pages

    def get_links(self, page):
        url = f'{self.url}'
        response = requests.get(url)
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')
        links = {}
        for a_tag in soup.find_all('a'):
            href = a_tag.get('href')
            text = a_tag.get_text(strip=True)
            if "月合集" in text:
                links[text] = href

        magnet_links = {}
        for title, link in links.items():
            response = requests.get(link)

            if response.status_code == 200:
                content = response.text
                matches = re.findall(r'\b[a-f0-9]{40}\b', content)
                if matches:
                    magnet_links[title] = f'magnet:?xt=urn:btih:{matches[0]}'
            else:
                print(f"请求失败，状态码: {response.status_code}")

        return magnet_links

    def update_json_file(self):
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            results = {}
            total_pages = self.get_pages()
            for i in range(1, total_pages + 1):
                new_data = self.get_links(i)
                results.update(new_data)
                print(f'Page {i} processed (Full Update)')
        else:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                results = json.load(file)

            total_pages = self.get_pages()
            for i in range(1, total_pages + 1):
                new_data = self.get_links(i)
                all_exists = True

                for title, magnet_link in new_data.items():
                    if title not in results or results[title] != magnet_link:
                        all_exists = False
                        break

                if not all_exists:
                    results = {**new_data, **results}
                    print(f'Page {i} processed (Incremental Update)')

                if all_exists:
                    print(f"第 {i} 页数据已存在于 JSON 文件中，停止更新")
                    break

        with open(self.filepath, 'w', encoding='utf-8') as file:
            json.dump(results, file, ensure_ascii=False, indent=4)

        print("JSON文件已更新")

# 使用示例
scraper = HACGScraper(url='https://www.hacg.mov/wp/page/1?s=%E5%90%88%E9%9B%86&submit=%E6%90%9C%E7%B4%A2', filepath=r"C:\Users\levywang\OneDrive\Code\avhub_v2\data\hacg.json")
scraper.update_json_file()



