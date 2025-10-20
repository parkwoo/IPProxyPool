"""Define different specific crawler classes for different proxy IP websites
As long as inheriting BaseSpider class and specifying specific url list, group XPATH and detail XPATH in the form of implementing class attributes,
a new crawler class can be implemented. Other methods are automatically inherited from BaseSpider class.
"""
from core.proxy_spider.base_spider import BaseSpider
from lxml import etree
from model import Proxy
from retrying import retry
import re
import json
from settings import TIMEOUT
from utils.http import get_request_headers
from utils.log import logger
import requests
import urllib3
urllib3.disable_warnings()

class Ip3366Spider(BaseSpider):
    """爬取ip3366网站的爬虫类"""
    # 列表页的url列表
    urls = [f"http://www.ip3366.net/free/?stype=1&page={i}" for i in range(1, 8)]
    # 分组XPATH
    group_xpath = "//*[@id='list']/table/tbody/tr"
    # 详情XPATH
    detail_xpath = {
        "ip": "./td[1]/text()",
        "port": "./td[2]/text()",
        "area": "./td[5]/text()",
    }

class ProxyListPlusSpider(BaseSpider):
    """爬取ProxyListPlus网站的爬虫类"""
    # 列表页的url列表
    urls = [f"https://list.proxylistplus.com/Fresh-HTTP-Proxy-List-{i}" for i in range(1, 7)]
    # 分组XPATH
    group_xpath = '//*[@id="page"]/table[2]/tr[position() > 2]'
    # 详情XPATH
    detail_xpath = {
        "ip": "./td[2]/text()",
        "port": "./td[3]/text()",
        "area": "./td[5]/text()",
    }

class KuaidailiSpider(BaseSpider):
    """爬取快代理网站的爬虫类"""
    # 列表页的url列表
    urls = [f"https://www.kuaidaili.com/free/inha/{i}/" for i in range(1, 11)]

    # Kuaidaili (Fast Proxy) occasionally has SSL errors in requests, so need to override get_page_from_url method
    # Set timeout and retry count
    @retry(stop_max_attempt_number=3, retry_on_result=lambda x: x is None)
    def get_page_from_url(self, url):
        """Request url to get page content"""
        try:
            response = requests.get(url, headers=get_request_headers(), timeout=TIMEOUT, verify=False)
            return response.content
        except Exception as e:
            logger.exception(f"Request {url} failed, error message is {e}")
            return None
    
    # Kuaidaili's proxy IPs have a different layout structure in the page compared to the first two crawlers
    # So need to override get_proxies_from_page method, use different extraction logic to parse page, get ip, port and area
    def get_proxies_from_page(self, page):
        """Extract ip, port and area from page and return encapsulated Proxy object"""
        # If page is empty, log and end method execution
        if page is None:
            logger.exception(f"Failed to get page")
            return
        # Decode the passed page parameter (bytes type) to get page content
        html_str = page.decode()
        # Use regular expression to extract string containing proxy IP information
        ip_list_str = re.search(r'const fpsList = (\[.*?\]);', html_str, re.S).group(1)
        # Convert string to json object (list of dictionaries containing proxy IP information)
        ip_list_json = json.loads(ip_list_str)
        # Iterate through this list
        for item in ip_list_json:
            # Extract ip
            ip = item['ip']
            # Extract port
            port = item['port']
            # Extract area
            area = item['location']
            # Return Proxy object
            yield Proxy(ip, port, area=area)

if __name__ == '__main__':
    # spider = Ip3366Spider()
    # spider = ProxyListPlusSpider()
    spider = KuaidailiSpider()
    for proxy in spider.get_proxies():
        print(proxy)
