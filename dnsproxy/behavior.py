"""DNS proxy response behavior module."""

from re import compile as regex_compile
from logging import getLogger

IP_REGEX_KEY = 'ipRegex'
STRATEGY_KEY = 'strategy'
ADDRESS_KEY = 'address'
MIN_LOG_LEVEL_KEY = 'minLogLevel'

class Behavior(object):
    """Behavior for given IP address. Creates response depending on set strategy.

    Call behavior.handles(req) to check if it's handling given IP.
    Call behavior.handle(req) to obtain response ready to be sent.
    """

    strategies = dict(
        block = lambda self, req: Behavior.block(self, req),
        forward = lambda self, req: Behavior.forward(self, req),
        respond = lambda self, req: Behavior.respond(self, req))

    def __init__(self, ip_regex = '', strategy = 'forward', address = None, min_log_level = 'DEBUG'):
        """Creates new behavior accepting IP address which is handled and strategy.
        
        """
        self.ip_regex = regex_compile(ip_regex)
        self.strategy = strategy
        self.address = address
        self.min_log_level = min_log_level
        self.logger = getLogger(__name__)

    def handles(self, req):
        """Checks whether given request's IP is handled by this behavior

        Returns True if it handles.
        """
        return self.ip_regex.match(req.ip) != None

    def handle(self, req):
        """Handles provided request according to set strategy.

        Returns response.
        """
        return self.strategies[self.strategy](req)

    def block(self, req):
        """Returns response with 'not found' content."""
        self.logger.info(str.format("Blocked request: {req}", req=req))

    def forward(self, req):
        """Returns response received from system resolver."""
        self.logger.info(str.format("Forwarded request: {req}", req=req))

    def respond(self, req):
        """Returns response containing self.address."""
        self.logger.info(str.format('Responded to request: {req}', req=req))

    def from_json(self, json):
        """Sets attributes from provided JSON object.

        Returns self.
        """
        self.ip_regex = regex_compile(json[IP_REGEX_KEY])
        self.strategy = json[STRATEGY_KEY]
        if ADDRESS_KEY in json:
            self.address = json[ADDRESS_KEY]
        else:
            self.address = None
        if MIN_LOG_LEVEL_KEY in json:
            self.min_log_level = json[MIN_LOG_LEVEL_KEY]
        else:
            self.min_log_level = 'DEBUG'
        return self

    def to_json(self):
        """Creates JSON object representing this Behavior.

        Returns created JSON object.
        """
        return {
            IP_REGEX_KEY : self.ip_regex.pattern,
            STRATEGY_KEY : self.strategy,
            ADDRESS_KEY : self.address,
            MIN_LOG_LEVEL_KEY : self.min_log_level }