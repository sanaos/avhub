# -*- encoding: utf-8 -*-
import re
import json
import os
from bs4 import BeautifulSoup
from curl_cffi import requests
from omegaconf import DictConfig
from utils.logger import setup_logger

class AVSpider:
    def __init__(self, av_code, source_url, proxy_url, use_proxy, cfg: DictConfig):
        self.source_url = source_url
        self.av_code = av_code.lower()
        self.proxy_url = proxy_url if use_proxy else None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
            'Content-Type': 'application/json'
        }
        self.proxies = {
            "http": self.proxy_url,
            "https": self.proxy_url
        } if self.proxy_url else {}
        self.logger = setup_logger(cfg)

    def get_video_url(self) -> list:
        """
        获取视频页面的链接。
        
        :return: 包含视频页面链接的列表。
        """
        code_str = self.av_code.replace('-', '')
        match = re.match(r'([a-zA-Z]+)(\d+)', code_str)
        if not match:
            self.logger.error(f"Invalid AV code format: {self.av_code}")
            return []

        letters, digits = match.groups()
        code_str = f"{letters.lower()}-{digits}"
        url = f"{self.source_url}{code_str}"
        try:
            response = requests.get(url, proxies=self.proxies, headers=self.headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Request Error: {e}")
            return []

        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')
        unique_links = set()

        for a_tag in soup.find_all('a'):
            alt_text = a_tag.get('alt')
            if alt_text and code_str in alt_text:
                href = a_tag.get('href')
                if href:
                    unique_links.add(href)

        self.logger.info(f"Found video URLs: {unique_links}")

        return list(unique_links)

    def get_magnet_links(self, link: str) -> list:
        """
        从视频页面中提取磁力链接。
        
        :param link: 视频页面的 URL。
        :return: 包含磁力链接的列表。
        """
        try:
            response = requests.get(link, proxies=self.proxies, headers=self.headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Request Error: {e}")
            return []

        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')
        target_table = soup.find('table', class_='min-w-full')

        result = []
        if target_table is not None:
            rows = target_table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                data = []

                for col in cols:
                    links = col.find_all('a', rel='nofollow')
                    if links:
                        for l in links:
                            href = l['href']
                            if "keepshare.org" not in href:
                                data.append(href)

                    text = col.get_text(strip=True)
                    if text != "下载" and "keepshare.org" not in text:
                        data.append(text)

                result.append(data)

        self.logger.info(f"Magnet links extracted from {link}")

        return result


class HacgSpider:
    def __init__(self, url, filepath, cfg: DictConfig):
        self.url = url
        self.filepath = filepath
        self.logger = setup_logger(cfg)

    def get_pages(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Request Error: {e}")
            return None

        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')
        div_ele = soup.find('div', class_='wp-pagenavi')
        page_text = div_ele.get_text() if div_ele else ''

        pages = None
        if "共" in page_text:
            pages = int(page_text.split('共')[1].split('页')[0])

        self.logger.info(f"Total pages found: {pages}")

        return pages

    def get_links(self, page):
        url = f'{self.url}page/{page}?s=%E5%90%88%E9%9B%86&submit=%E6%90%9C%E7%B4%A2'
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Request Error: {e}")
            return {}

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
            try:
                response = requests.get(link)
                response.raise_for_status()
            except requests.RequestException as e:
                self.logger.error(f"Request Error: {e}")
                continue

            content = response.text
            matches = re.findall(r'\b[a-f0-9]{40}\b', content)
            if matches:
                magnet_links[title] = f'magnet:?xt=urn:btih:{matches[0]}'

        self.logger.info(f"Magnet links extracted from page {page}")

        return magnet_links

    def update_json_file(self):
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            results = {}
            total_pages = self.get_pages()
            if total_pages is None:
                self.logger.error("Unable to get total")
                return

            for i in range(1, total_pages + 1):
                new_data = self.get_links(i)
                results.update(new_data)
                self.logger.info(f'Page {i} processed (Full Update)')
        else:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                results = json.load(file)

            total_pages = self.get_pages()
            if total_pages is None:
                self.logger.error("Unable to get total")
                return

            for i in range(1, total_pages + 1):
                new_data = self.get_links(i)
                all_exists = True

                for title, magnet_link in new_data.items():
                    if title not in results or results[title] != magnet_link:
                        all_exists = False
                        break

                if not all_exists:
                    results = {**new_data, **results}
                    self.logger.info(f'Page {i} processed (Incremental Update)')

                if all_exists:
                    self.logger.info(f"Page {i} data already exists in the JSON file, stop updating")
                    break

        with open(self.filepath, 'w', encoding='utf-8') as file:
            json.dump(results, file, ensure_ascii=False, indent=4)

        self.logger.info("JSON file updated")