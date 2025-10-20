"""
Goal:
    Provide a Web service interface for high availability proxy IPs for web scrapers
Steps:
    1. Implement a service to randomly obtain high availability proxy IPs based on protocol type and domain
    2. Implement a service to obtain multiple high availability proxy IPs based on protocol type and domain
    3. Implement a service to add unavailable domains to a specified IP
Implementation:
    - In proxy_api.py, create a ProxyApi class
    - Implement initialization method
        - Initialize a Flask Web service
    - Implement a service to randomly obtain high availability proxy IPs based on protocol type and domain
        - IP can be filtered by protocol and domain parameters
        - protocol: Current request protocol type
        - domain: Current request domain
    - Implement a service to obtain multiple high availability proxy IPs based on protocol type and domain
        - IP can be filtered by protocol and domain parameters
    - Implement a service to add unavailable domains to a specified IP
        - If a domain parameter is specified when obtaining IP, that IP will not be retrieved, thus further improving proxy IP availability
    - Implement run method to start Flask WEB service
    - Implement start class method to start service via class name
"""

from flask import Flask
from flask import request
from core.db.mongo_pool import MongoPool
from settings import MAX_PROXIES_RANGE
from settings import WEB_API_PORT   
import json


class ProxyApi:
    def __init__(self):
        """Initialization method"""
        # Initialize Flask's Web service
        self.app = Flask(__name__)
        # Initialize MongoDB database operation object
        self.mongo_pool = MongoPool()

        # Provide a service for random high availability proxy IP based on protocol type and domain
        @self.app.route("/random")
        def random():
            # Get protocol type from request parameters
            protocol = request.args.get("protocol")
            # Get domain from request parameters
            domain = request.args.get("domain")
            # Randomly get a high availability proxy IP from MongoDB database based on specified protocol and domain
            # Range for random proxy IP retrieval is specified in configuration file as MAX_PROXIES_RANGE
            proxy = self.mongo_pool.get_random_proxy(
                protocol=protocol, domain=domain, count=MAX_PROXIES_RANGE
            )

            # If proxy IP is obtained
            if proxy:
                # If protocol is not empty, return protocol://IP:port
                if protocol:
                    return f"{protocol}://{proxy.ip}:{proxy.port}"
                else:
                    # If protocol is empty, return IP:port
                    return f"{proxy.ip}:{proxy.port}"
            else:
                # If proxy IP cannot be obtained, return that proxy IP with specified conditions does not exist
                return "Proxy IP with specified conditions does not exist"

        # Provide a service to get multiple high availability proxy IPs based on protocol type and domain
        @self.app.route("/proxies")
        def proxies():
            # Get protocol type from request parameters
            protocol = request.args.get("protocol")
            # Get domain from request parameters
            domain = request.args.get("domain")
            # Get multiple high availability proxy IPs from MongoDB database based on specified protocol and domain
            # Range for getting proxy IPs is specified in configuration file as MAX_PROXIES_RANGE
            proxies = self.mongo_pool.get_proxies(
                protocol=protocol, domain=domain, count=MAX_PROXIES_RANGE
            )

            # If list of proxy IPs with specified conditions is obtained (in form of proxy objects)
            if proxies:
                # Convert proxy object list to dictionary list for easy json serialization
                proxies = [proxy.__dict__ for proxy in proxies]
                # Return json formatted proxy IP list
                return json.dumps(proxies, ensure_ascii=False, indent=2)
            else:
                # If proxy IPs with specified conditions cannot be obtained, return that proxy IPs with specified conditions do not exist
                return "Proxy IPs with specified conditions do not exist"

        # Service to add unavailable domains to a specified IP
        @self.app.route("/disable_domain")
        def disable_domain():
            # Get IP from request parameters
            ip = request.args.get("ip")
            # Get domain from request parameters

            # If IP parameter is empty, return prompt message
            if not ip:
                return "Please provide IP"
            # If domain parameter is empty, return prompt message
            if not domain:
                return "Please provide domain"

            # If specified IP does not exist, return prompt message
            if len(self.mongo_pool.find(conditions={"_id": ip})) == 0:
                return "Specified proxy IP does not exist"

            # Add unavailable domain to specified IP
            self.mongo_pool.disable_domain(ip=ip, domain=domain)
            # Return success message for adding unavailable domain
            return f"Successfully disabled domain {domain} for {ip}"

    def run(self):
        """Start Flask's Web service"""
        self.app.run("0.0.0.0", port=WEB_API_PORT)

    @classmethod
    def start(cls):
        """Class method as entry point to start the entire Flask Web service"""
        # Initialize ProxyApi class
        proxy_api = cls()
        # Start Flask Web service
        proxy_api.run()


if __name__ == "__main__":
    ProxyApi.start()
