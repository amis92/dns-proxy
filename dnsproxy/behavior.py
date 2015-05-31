"""DNS proxy response behavior module."""

from re import compile as regex_compile, match
from logging import getLogger

IP_KEY = 'ip'
STRATEGY_KEY = 'strategy'
DEFAULT_STRATEGY = 'forward'
ADDRESS_KEY = 'address'
MIN_LOG_LEVEL_KEY = 'minLogLevel'
DEFAULT_MIN_LOG_LEVEL = 'DEBUG'

class Behavior(object):
    """Behavior for given address. Creates response depending on set strategy.

    Call behavior.handles(req) to check if it's handling given address.
    Call behavior.handle(req) to obtain response ready to be sent.
    """

    strategies = dict(
        block = lambda self, req: Behavior.block(self, req),
        forward = lambda self, req: Behavior.forward(self, req),
        respond = lambda self, req: Behavior.respond(self, req))

    def __init__(self, address = '', strategy = DEFAULT_STRATEGY, ip = '', min_log_level = DEFAULT_MIN_LOG_LEVEL):
        """Creates new behavior accepting address which is handled and strategy.
        
        """
        self.ip = ip
        self.strategy = strategy
        self.address = address
        self.min_log_level = min_log_level
        self.logger = getLogger(__name__)

    def handles(self, req):
        """Checks whether given request's address is handled by this behavior

        Returns True if it handles.
        """
        return match(self.address, req.address) != None

    def handle(self, req):
        """Handles provided request according to set strategy.

        Returns response.
        """
        return self.strategies[self.strategy](req)

    def block(self, req):
        """Returns response with 'not found' content."""
        self.logger.info(str.format("Blocked request: {req}", req=req))
        # TODO return meaningful block response

    def forward(self, req):
        """Returns response received from system resolver."""
        self.logger.info(str.format("Forwarded request: {req}", req=req))
        # TODO return meaningful forward response

    def respond(self, req):
        """Returns response containing self.ip."""
        self.logger.info(str.format('Responded to request: {req}', req=req))
        # TODO return meaningful generated address response

    def from_json(self, json):
        """Sets attributes from provided JSON object/dict.

        Returns self.
        """
        self.address = json[ADDRESS_KEY]
        self.strategy = json[STRATEGY_KEY]
        if IP_KEY in json:
            self.ip = json[IP_KEY]
        else:
            self.ip = ''
        if MIN_LOG_LEVEL_KEY in json:
            self.min_log_level = json[MIN_LOG_LEVEL_KEY]
        else:
            self.min_log_level = DEFAULT_MIN_LOG_LEVEL
        return self

    def to_json(self):
        """Creates JSON object/dict representing this Behavior.

        Returns created JSON object (dict).
        """
        return {
            IP_KEY : self.ip,
            STRATEGY_KEY : self.strategy,
            ADDRESS_KEY : self.address,
            MIN_LOG_LEVEL_KEY : self.min_log_level }