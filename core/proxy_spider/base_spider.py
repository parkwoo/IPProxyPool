"""
Implement a general crawler
 -Goal: Implement a general crawler that can specify different URL lists, group XPATH and detail XPATH, to extract proxy IP, port number and region from different pages;
 - Steps:
      1. In base_spider.py file, define a BaseSpider class
      2. Provide three class member variables:
          - urls: List of URLs for proxy IP websites
          - group_xpath: Group XPATH, XPATH to get list of tags containing proxy IP information
          - detail_xpath: Detail XPATH, XPATH to get proxy IP detail information, format: {'ip':'xx', 'port':'xx', 'area':'xx'}
      3. Provide initial method, pass in crawler URL list, group XPATH, detail (group) XPATH
      4. Provide an external method to get proxy IP
          - Iterate through URL list, get URL
          - Send request according to URL, get page data
          - Parse page, extract data, encapsulate as Proxy object
          - Return Proxy object list
"""
from lxml import etree
import requests
from utils.http import get_request_headers
from model import Proxy 
import random
import time


class BaseSpider:

    urls = []         # List of URLs for proxy IP websites
    group_xpath = ''  # Group XPATH, XPATH to get list of tags containing proxy IP information
    detail_xpath = {} # Detail XPATH, XPATH to get proxy IP detail information, format: {'ip':'xx', 'port':'xx', 'area':'xx'}

    def __init__(self, urls=[], group_xpath='', detail_xpath={}):
        """Initialization method, pass in crawler URL list, group XPATH, detail (group) XPATH
        Only when parameters are explicitly passed in, will the passed in parameters be used, otherwise use default values of class member variables
        """
        if urls:
            self.urls = urls
        if group_xpath:
            self.group_xpath = group_xpath
        if detail_xpath:
            self.detail_xpath = detail_xpath


    def get_page_from_url(self, url):
        """Request url to get page content"""
        response = requests.get(url, headers=get_request_headers())
        return response.content

    def _get_first_from_list(self, lis):
        """Get the first element from the list, if the list is empty, return an empty string"""
        return lis[0] if len(lis) != 0 else ''

    def get_proxies_from_page(self, page):
        """Extract ip, port and area from page and return encapsulated Proxy object"""
        # Use lxml's etree module to parse page
        html = etree.HTML(page)
        # Use group xpath to extract list of tags containing proxy IP information
        trs = html.xpath(self.group_xpath)
        # Iterate through group tag list
        for tr in trs:
            # Use _get_first_from_list method to extract ip, port and area
            # Can return empty string when no content is extracted, avoiding errors that may occur from direct index usage
            # Extract ip
            ip = self._get_first_from_list(tr.xpath(self.detail_xpath['ip']))
            # Extract port
            port = self._get_first_from_list(tr.xpath(self.detail_xpath['port']))
            # Extract area
            area = self._get_first_from_list(tr.xpath(self.detail_xpath['area']))
            # Return Proxy object
            yield Proxy(ip, port, area=area)
        
        
    def get_proxies(self):
        """Method to get all proxy IPs from a website
        """
        # Iterate through URL list, get URL
        for url in self.urls:
            # Randomly sleep 1-3 seconds to prevent IP blocking or abnormal data return due to frequent requests
            time.sleep(random.uniform(1, 3))
            # Send request according to URL, get page data
            page = self.get_page_from_url(url)
            # Parse page, extract data, encapsulate as Proxy object
            # proxies = self.get_proxies_from_page(page)
            proxies = self.get_proxies_from_page(page)
            # Return Proxy object generator
            yield from proxies


if __name__ == '__main__':
    config = {
        'urls': [f'http://www.ip3366.net/free/?stype=1&page={i}' for i in range(1, 4)],
        'group_xpath':"//*[@id='list']/table/tbody/tr",
        'detail_xpath': {
            'ip': './td[1]/text()',
            'port': './td[2]/text()',
            'area': './td[5]/text()'
        }
    }
    spider = BaseSpider(urls=config['urls'], group_xpath=config['group_xpath'], detail_xpath=config['detail_xpath'])
    for proxy in spider.get_proxies():
        print(proxy)
