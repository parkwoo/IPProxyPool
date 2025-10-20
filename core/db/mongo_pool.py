import random
"""
Proxy pool database module
- Purpose: Perform database operations on the proxies collection
- Goal: Implement database CRUD operations
- Steps:
  1. Define MongoPool class
  2. Implement initialization method, establish data connection, get collection to operate
 3. Implement insert function
  4. Implement update function
  5. Implement save function, insert if not exists, update if exists
  6. Implement query function: Query according to conditions, can specify query count, sort by score descending then speed ascending to ensure quality proxy IPs are at the top
  7. Implement delete function: Delete proxy according to proxy IP
  8. Implement getting proxy IP list according to protocol type and website domain to access
  9. Implement getting a random proxy IP according to protocol type and complete domain to access
"""
import pymongo
from model import Proxy
from settings import MONGO_URL, DATABASE, COLLECTION
from utils.log import logger

class MongoPool:
    def __init__(self):
        """Initialize"""
        # Establish database connection
        self.client = pymongo.MongoClient(MONGO_URL)
        # Get collection to operate
        self.proxies = self.client[DATABASE][COLLECTION]
        

    def insert_one(self, proxy):
        """Save proxy IP to database"""

        # Check if proxy IP exists
        count = self.proxies.count_documents({'_id': proxy.ip})
        # If proxy IP does not exist, insert
        if count == 0:
            dic = proxy.__dict__
            dic['_id'] = proxy.ip
            self.proxies.insert_one(dic)
            logger.info(f'insert success: {proxy}')
        # If proxy IP exists, print proxy IP already exists
        else:
            logger.warning(f'Proxy already existed: {proxy}')

    def update_one(self, proxy):
        """Update proxy IP"""
        self.proxies.update_one({'_id': proxy.ip}, {'$set': proxy.__dict__})

    def delete_one(self, proxy):
        """Delete proxy IP"""
        self.proxies.delete_one({'_id': proxy.ip})

    def find_all(self):
        """Query all proxy IPs"""
        cursor = self.proxies.find()
        for item in cursor:
            item.pop('_id')
            yield Proxy(**item)

    def find(self, conditions={}, count=0):
        """Query proxy IP according to conditions, can specify query count, sort by score descending, then speed ascending to ensure quality proxy IPs are at the top
        :param conditions: Query conditions
        :param count: Query count
        :return: Return list of proxy IPs that meet conditions
        """
        # Query proxy IP according to conditions
        cursor = self.proxies.find(conditions, limit=count).sort([
            ('score', pymongo.DESCENDING), ('speed', pymongo.ASCENDING)
        ])

        # Convert query results to list
        proxy_list = list()
        for item in cursor:
            item.pop('_id')
            proxy_list.append(Proxy(**item))
        
        return proxy_list

    def get_proxies(self, protocol=None, domain=None, nick_type=0, count=0):
        """
        Get proxy IP list according to protocol type, website domain to access and anonymity level, can specify number of proxy IPs to get
        :param protocol: Protocol type (http, https), default value is None, indicating support for both http and https
        :param domain: Website domain to access, default value is None, indicating no domain specified
        :param count: Query count, default value is 0, indicating no count specified
        :param nick_type: Anonymity level (High anonymity: 0, Anonymous: 1, Transparent: 2), default value is 0, indicating high anonymity
        :return: Return list of proxy IPs that meet conditions
        """
        # Initialize query conditions
        conditions = {'nick_type': nick_type}

        # Set query conditions according to protocol type
        # If protocol type is None, indicates querying proxy IPs that support both http and https, protocol value is 2
        if protocol is None:
            conditions['protocol'] = 2
        # If protocol type is http, indicates querying proxy IPs that support http, protocol value is 0 or 2
        elif protocol.lower() == 'http':
            conditions['protocol'] = {'$in': [0, 2]}
        # If protocol type is https, indicates querying proxy IPs that support https, protocol value is 1 or 2
        else:
            conditions['protocol'] = {'$in': [1, 2]}

        # If domain is None, indicates no domain specified
        # Otherwise set query conditions according to domain
        if domain:
            conditions['disable_domains'] = {'$nin': [domain]}

        # Call find method to query proxy IP
        return self.find(conditions=conditions, count=count)
    
    def get_random_proxy(self, protocol=None, domain=None, nick_type=0, count=0):
        """Randomly get a proxy IP according to protocol type, website domain to access and anonymity level
        :param protocol: Protocol type (http, https), default value is None, indicating support for both http and https
        :param domain: Website domain to access, default value is None, indicating no domain specified
        :param nick_type: Anonymity level (High anonymity: 0, Anonymous: 1, Transparent: 2), default value is 0, indicating high anonymity
        :param count: Range for getting random proxy IP, default value is 0, indicating randomly get one from all proxy IPs that meet conditions
        :return: Return a proxy IP that meets conditions
        """
        # Call get_proxies method to get list of proxy IPs that meet conditions
        proxy_list = self.get_proxies(protocol=protocol, domain=domain, nick_type=nick_type, count=count)
        # If proxy IP list is not empty, randomly return a proxy IP
        if proxy_list:
            return random.choice(proxy_list)
        # If proxy IP list is empty, return None
        else:
            return None

    def disable_domain(self, ip, domain):
        """Add specified domain to the unavailable domain list of specified proxy IP"""
        # Check if specified domain already exists in the unavailable domain list of specified proxy IP
        # If it does not exist, add it
        if self.proxies.count_documents({'_id': ip, 'disable_domains': domain}) == 0:
            self.proxies.update_one({'_id': ip}, {'$push': {'disable_domains': domain}})

    def close(self):
        """Close database connection"""
        self.client.close()

    def __del__(self):
        """Close database connection"""
        try:
            self.close()
        except Exception as e:
            logger.error(f'Error closing MongoDB client: {e}')

if __name__ == '__main__':
    from model import Proxy

    mongo = MongoPool()

    proxy1 = Proxy('124.89.97.43', '80', protocol=1, score=10, nick_type=0, speed=0.38, disable_domains=['baidu.com'])
    proxy2 = Proxy('124.89.97.40', '80', protocol=2, score=12, nick_type=2, speed=0.37, disable_domains=['taobao.com']  )
    proxy3 = Proxy('124.89.97.44', '80', protocol=1, score=9, nick_type=0, speed=0.30, disable_domains=['google.com'])
    proxy4 = Proxy('124.89.97.45', '80', protocol=0, score=22, nick_type=1, speed=0.31, disable_domains=['jd.com'])

    mongo.disable_domain(proxy1.ip, 'baidu.com')
