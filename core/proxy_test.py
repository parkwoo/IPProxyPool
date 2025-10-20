from gevent import monkey
monkey.patch_all() # Apply patch to let gevent recognize time-consuming operations

from gevent.pool import Pool
from core.db.mongo_pool import MongoPool
from core.proxy_validate.httpbin_validator import check_proxy
from settings import MAX_SCORE, TEST_PROXY_ASYNC_COUNT, RUN_TEST_INTERVAL_HOURS
from utils.log import logger
from queue import Queue
import schedule
import time


class ProxyTester:
    def __init__(self):
        """Initialization method"""
        # Database operation object
        self.mongo_pool = MongoPool()
        # Coroutine pool
        self.gevent_pool = Pool()
        # Queue for passing proxy objects
        self.queue = Queue()

    def run(self):
        """Core logic for executing the proxy IP testing process"""
        # Get all proxy objects of proxy IPs from database
        proxies = self.mongo_pool.find_all()
        # Iterate through proxy objects
        for proxy in proxies:
            # Put proxy to be tested into queue
            self.queue.put(proxy)
        # Create concurrent coroutines in coroutine pool according to configured concurrency count
        for _ in range(TEST_PROXY_ASYNC_COUNT):
            # Add method to test one proxy to coroutine pool and specify callback function
            self.gevent_pool.apply_async(
                self.__check_one_proxy, callback=self.__check_callback
            )
        # Block thread to wait for all tasks in queue to complete
        self.queue.join()

    def __check_callback(self, temp):
        """Callback function
        Continuously call itself to achieve a loop (continuously add proxy testing method to coroutine pool)
        """
        self.gevent_pool.apply_async(
            self.__check_one_proxy, callback=self.__check_callback
        )

    def __check_one_proxy(self):
        """Specific logic implementation for testing a Proxy"""
        # Get proxy to be tested from queue
        proxy = self.queue.get()
        # Test proxy
        proxy = check_proxy(proxy)
        # If speed=-1, indicates unavailable
        if proxy.speed == -1:
            # Decrease score by one
            proxy.score -= 1
            # If score becomes 0, delete from database
            if proxy.score == 0:
                self.mongo_pool.delete_one(proxy)
                logger.info(f"Delete proxy: {proxy}")
            # If score is not 0, update proxy to database
            else:
                self.mongo_pool.update_one(proxy)
        else:
            # If speed!=-1, indicates available, restore default maximum score
            proxy.score = MAX_SCORE
            # And update to database
            self.mongo_pool.update_one(proxy)
        # Notify queue that current task is completed, decrease counter
        self.queue.task_done()
    
    @classmethod
    def start(cls):
        """Entry method for starting the proxy testing module
        Use schedule module to execute a testing task at regular intervals
        """
        # Create instance
        proxy_tester = cls()
        # Start immediately, otherwise need to wait one cycle to start
        proxy_tester.run()
        # According to configuration file settings, specify the execution cycle of the instance's run method
        schedule.every(RUN_TEST_INTERVAL_HOURS).hours.do(proxy_tester.run)
        # Continuously check schedule status and activate execution when cycle arrives
        while True:
            # Check cycle status every 1 second
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    ProxyTester.start()
