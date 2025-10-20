"""Define the data model for the proxy object"""
from settings import MAX_SCORE

class Proxy:
    def __init__(self, ip, port, protocol=-1, nick_type=-1, speed=-1, area=None, score=MAX_SCORE, disable_domains=None):
        """Initialize the proxy object.
        :param ip: IP address of the proxy.
        :param port: Port number of the proxy IP.
        :param protocol: Protocol type supported by the proxy IP. http is 0, https is 1, both https and http support is 2. Default is -1.
        :param nick_type: Anonymity level of the proxy IP. High anonymity: 0, Anonymous: 1, Transparent: 2. Default is -1.
        :param speed: Response speed of the proxy IP, in seconds. Default is -1.
        :param area: Region where the proxy IP is located. Default is None.
        :param score: Score of the proxy IP, used to measure the availability of the proxy. The default score can be configured in the configuration file. During proxy availability checks, 1 point is deducted for each request failure, and when it reaches 0, it is deleted from the pool. If the proxy is found to be available, the default score is restored. Default is MAX_SCORE.
        :param disable_domains: List of disabled domains. Some proxy IPs are unavailable under certain domains, but available under other domains. Default is an empty list.
        """
        self.ip = ip
        self.port = port
        self.protocol = protocol
        self.nick_type = nick_type
        self.speed = speed
        self.area = area
        self.score = score
        self.disable_domains = disable_domains or []
    
    def __str__(self):
        return str(self.__dict__)
