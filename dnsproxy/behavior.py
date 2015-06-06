"""DNS proxy response behavior module."""

from re import compile as regex_compile, match
from logging import getLogger
from dnslib import RR, A, QTYPE
from dns.exception import DNSException
import dns.resolver

IP_KEY = 'ip'
STRATEGY_KEY = 'strategy'
DEFAULT_STRATEGY = 'forward'
ADDRESS_KEY = 'address'
MIN_LOG_LEVEL_KEY = 'minLogLevel'
DEFAULT_MIN_LOG_LEVEL = 'DEBUG'

class Behavior(object):
    """Behavior for given address. Creates response depending on set strategy.

    Call behavior.handles(address) to check if it's handling given address.
    Call behavior.handle(request) to obtain dns response or None if no response should be sent.
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

    def handles(self, address):
        """Checks whether given address is handled by this behavior

        Returns True if it handles.
        """
        return match(self.address, address) != None

    def handle(self, request):
        """Handles provided request according to set strategy.

        Returns response or None if no response should be sent.
        """
        return self.strategies[self.strategy](request)

    def block(self, request):
        """Returns None."""
        address = str(request.questions[0].qname)
        self.logger.info(str.format('Blocking request: {addr}', addr=address))
        return None

    def forward(self, request):
        """Returns response received from system resolver."""
        address = str(request.questions[0].qname)
        self.logger.info(str.format('Forwarding request: {addr}', addr=address))
        try:
            answers = dns.resolver.query(address, 'A')
        except DNSException:
            self.logger.exception(str.format('Exception when forwarding request: {addr}', addr=address))
        response = request.reply()
        for rdata in answers:
            ip = rdata.address
            response.add_answer(RR(address, QTYPE.A, rdata=A(ip)))
        return response

    def respond(self, request):
        """Returns response containing self.ip."""
        address = str(request.questions[0].qname)
        self.logger.info(str.format('Responding to request for: {addr} with ip={ip}', addr=address, ip = self.ip))
        response = request.reply()
        response.add_answer(RR(address, QTYPE.A, rdata=A(self.ip)))
        return response

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

def first_or_default(request, behaviors):
    """Finds a behavior in list of behaviors,
    which handles given request.

    Returns behavior if any is found, or default behavior otherwise.
    """
    address = str(request.questions[0].qname)
    if behaviors == None or len(behaviors) == 0:
        return Behavior(address)
    for behavior in behaviors:
        if (behavior.handles(address)):
            return behavior
    return Behavior(address)
