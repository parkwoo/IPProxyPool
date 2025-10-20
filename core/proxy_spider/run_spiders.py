"""
- Goal: According to configuration file information, load crawlers, crawl proxy IPs, validate them, and if available, write them to the database
- Approach:
    - In run_spider.py, create RunSpider class
    - Provide a run method for running crawlers, as the entry point for running crawlers, implementing core processing logic
        - According to configuration file information, get crawler object list.
        - Get crawler objects, iterate through crawler object's get_proxies method, get proxy IPs
        - Test proxy IPs (proxy IP testing module)
        - If available, write to database (database module)
        - Handle exceptions to prevent one crawler from failing internally and affecting other crawlers.
    - Use asynchronous execution for each crawler task to improve proxy IP crawling efficiency
        - Create coroutine pool object in init method
        - Extract code for handling one proxy crawler into a method
        - Use asynchronous execution for this method
        - Call coroutine's join method to make current thread wait for coroutine task completion.
    - Use schedule module to execute a crawling task at regular intervals
        - Define a start class method
        - Create current class object, call run method
        - Use schedule module to execute current object's run method at regular intervals
"""
from gevent import monkey
monkey.patch_all()  # Apply patch to let gevent recognize time-consuming operations
import importlib
from settings import PROXIES_SPIDERS
from core.proxy_validate.httpbin_validator import check_proxy
from core.db.mongo_pool import MongoPool
from utils.log import logger
from gevent.pool import Pool
import schedule
import time
from settings import RUN_SPIDERS_INTERVAL_HOURS


class RunSpider:
    def __init__(self):
        """Initialization method
        Get database operation object
        """
        self.mongo_pool = MongoPool()
        self.gevent_pool = Pool()

    def get_spider_from_settings(self):
        """According to configuration file information, return crawler object list"""
        for path in PROXIES_SPIDERS:
            # Parse crawler module name and crawler class name from configuration string
            module_name, cls_name = path.rsplit('.', maxsplit=1)
            # Dynamically load crawler module
            module = importlib.import_module(module_name)
            # Get crawler object from crawler module
            spider_cls = getattr(module, cls_name)
            # Create crawler instance and return via generator
            spider = spider_cls()
            yield spider


    def __execute_one_spider_task(self, spider):
        """Extract code for handling one crawler into this method"""
        # Handle exceptions to prevent one crawler from failing internally and affecting other crawlers.
        try:
            # Iterate through crawler object's get_proxies method to get Proxy objects corresponding to proxy IPs
            for proxy in spider.get_proxies():
                # Test proxy IP (proxy IP testing module)
                print(f'Testing: {proxy}')
                proxy = check_proxy(proxy)
                # If proxy IP is available (speed is not -1), save to database
                if proxy.speed != -1:
                    self.mongo_pool.insert_one(proxy)
        # Catch exceptions, print exception information
        except Exception as e:
            logger.exception(e)


    def run(self):
        """Provide a run method for running crawlers, as the entry point for running crawlers, implementing core processing logic
        """
        # Get crawler object generator
        spiders = self.get_spider_from_settings()
        # Iterate through crawler objects
        for spider in spiders:
            # Execute each crawler's task using asynchronous coroutines
            self.gevent_pool.apply_async(self.__execute_one_spider_task, args=(spider, ))
        # Block main thread to wait for all coroutine tasks to complete
        self.gevent_pool.join()

    
    @classmethod
    def start(cls):
        """Class method as startup entry
        Use schedule module to execute a crawling task at regular intervals
        """
        # Create instance
        run_spider = cls()
        # Start immediately, otherwise need to wait one cycle to start
        run_spider.run()
        # Specify the execution cycle of the instance's run method
        schedule.every(RUN_SPIDERS_INTERVAL_HOURS).hours.do(run_spider.run)
        # Continuously check schedule status, activate execution when cycle arrives
        while True:
            # Check cycle status every second
            schedule.run_pending()
            time.sleep(1)


if __name__ == '__main__':
    RunSpider.start()
