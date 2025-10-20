import requests
import json
import time
from settings import TIMEOUT
from utils.http import get_request_headers
from utils.log import logger
from model import Proxy

def check_proxy(proxy):
    """Check if proxy IP is available"""
    # Set proxies parameter of requests module according to proxy object to be checked
    proxies = {
        "http": f'http://{proxy.ip}:{proxy.port}',
        "https": f'https://{proxy.ip}:{proxy.port}'
    }

    # Check http proxy IP
    is_http, http_nick_type, http_speed = _check_http_proxy(proxies)
    # Check https proxy IP
    is_https, https_nick_type, https_speed = _check_http_proxy(proxies, is_http=False)

    # If both http and https are supported, set protocol type to 2
    if is_http and is_https:
        proxy.protocol = 2
        proxy.nick_type = http_nick_type  # If both are supported, use http's anonymity type as reference
        proxy.speed = http_speed          # If both are supported, use http's speed as reference
    # If only http is supported, set protocol type to 0
    elif is_http:
        proxy.protocol = 0
        proxy.nick_type = http_nick_type
        proxy.speed = http_speed
    # If only https is supported, set protocol type to 1
    elif is_https:
        proxy.protocol = 1
        proxy.nick_type = https_nick_type
        proxy.speed = https_speed
    # If neither is supported, set protocol type, anonymity type, and speed to -1
    # Indicate that the proxy IP is unavailable
    else:
        proxy.protocol = -1
        proxy.nick_type = -1
        proxy.speed = -1
    
    # Return the checked proxy object
    return proxy

def _check_http_proxy(proxies, is_http=True):
    """Check if http or https proxy IP is available"""
    # Initialize anonymous type and speed to -1
    nick_type = -1
    speed = -1

    # If is_http is True, check if proxy IP supports http
    if is_http:
        test_url = "http://www.httpbin.org/get"
    # Otherwise check if proxy IP supports https
    else:
        test_url = "https://www.httpbin.org/get"
    
    # Set timeout (imported from configuration file)
    timeout = TIMEOUT
    # Get random request headers
    req_headers = get_request_headers()
    try:
        # Record start time
        start = time.perf_counter()
        # Send request, get response
        response = requests.get(test_url, proxies=proxies, headers=req_headers, timeout=timeout)
        # If request is successful
        if response.ok:
            # Record end time
            end = time.perf_counter()
            # Calculate the difference between end time and start time, which is the speed of the proxy IP, in seconds,保留 two decimal places
            speed = round(end - start, 2)

            # Get response content
            content = json.loads(response.text)
            # Get response headers
            res_headers = content['headers']
            # Get source IP detected by httpbin
            origin = content['origin']
            # Get proxy connection detected by httpbin
            proxy_connection = res_headers.get('Proxy-Connection')

            # Determine the anonymity type of the proxy IP
            # If origin contains a comma, it indicates that origin contains two IPs, indicating that httpbin detected the existence of the proxy IP
            # Then it indicates that the proxy IP is a transparent proxy, and the value of nick_type is 2
            if ',' in origin:
                nick_type = 2
            # Otherwise: if Proxy-Connection field exists, it indicates that the proxy IP is an ordinary anonymous proxy, and the value of nick_type is 1
            elif proxy_connection:
                nick_type = 1
            # Otherwise: indicates that the proxy IP is a high anonymous proxy, and the value of nick_type is 0
            else:
                nick_type = 0
            
            # Return True boolean value indicating proxy IP availability, anonymity type and speed
            return True, nick_type, speed
        # If request fails, return False boolean value indicating proxy IP unavailability, anonymity type (-1) and speed (-1)
        else:
            return False, nick_type, speed
    except Exception as e:
        # If an exception occurs during the entire detection process, return False boolean value indicating proxy IP unavailability, anonymity type (-1) and speed (-1)
        return False, nick_type, speed

if __name__ == '__main__':
    proxy = Proxy(ip='5.58.97.89', port='61710')
    print(check_proxy(proxy))
