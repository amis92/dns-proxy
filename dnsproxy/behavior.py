"""DNS proxy response behavior module."""

from re import compile as regex_compile, match
from dnslib import RR, A, QTYPE
from dns.exception import DNSException
import dns.resolver
import logging

module_logger = logging.getLogger('dnsproxy.behavior')

IP_KEY = 'ip'
STRATEGY_KEY = 'strategy'
DEFAULT_STRATEGY = 'forward'
ADDRESS_KEY = 'address'
LOGLEVEL_KEY = 'logLevel'
DEFAULT_LOGLEVEL = 'DEBUG'

def getLogLevelNumber(loglevelname):
    """Parses log level name into log level number.
   
    Returns int value of log level. On failure, DEBUG level value is returned."""
    number = getattr(logging, loglevelname, None)
    if not isinstance(number, int):
        module_logger.debug("failed to parse log level name '{name}'".format(name = loglevelname))
        number = logging.DEBUG
    return number

class Behavior(object):
    """Behavior for given address. Creates response depending on set strategy.

    Call behavior.handles(address) to check if it's handling given address.
    Call behavior.handle(request) to obtain dns response or None if no response should be sent.
    """

    strategies = dict(
        block = lambda self, req: Behavior.block(self, req),
        forward = lambda self, req: Behavior.forward(self, req),
        respond = lambda self, req: Behavior.respond(self, req))

    def __init__(self, address = '', strategy = DEFAULT_STRATEGY, ip = '', loglevel = DEFAULT_LOGLEVEL):
        """Creates new behavior accepting address which is handled and strategy.
        
        """
        self.logger = logging.getLogger('dnsproxy.behavior.Behavior')
        self.ip = ip
        self.strategy = strategy
        self.address = address
        self.loglevel = loglevel

    def __str__(self):
        return "Behavior(address='{addr}', strategy='{strategy}', ip = '{ip}', log_level = '{loglevel}')".format(
            addr = self.address,
            strategy = self.strategy,
            ip = self.ip,
            loglevel = self.loglevel)

    def parseloglevel(self):
        return getLogLevelNumber(self.loglevel)

    def handles(self, address):
        """Checks whether given address is handled by this behavior

        Returns True if it handles.
        """
        m = match(self.address, address)
        self.logger.debug("handles check: address '{addr}' by {b}, result: {r}".format(b = str(self), addr=address, r = m != None))
        return m != None

    def handle(self, request):
        """Handles provided request according to set strategy.

        Returns response or None if no response should be sent.
        """
        self.logger.debug("handle: {b}, request: {r}".format(b = str(self), r = request))
        return self.strategies[self.strategy](self, request)

    def block(self, request):
        """Returns None."""
        address = str(request.questions[0].qname)
        self.logger.log(self.parseloglevel(), "{b} - Blocking request for address:'{addr}'".format(addr=address, b=str(self)))
        return None

    def forward(self, request):
        """Returns response received from system resolver."""
        address = str(request.questions[0].qname)
        self.logger.log(self.parseloglevel(), "{b} - Forwarding request for address:'{addr}'".format(addr=address, b=str(self)))
        try:
            answers = dns.resolver.query(address, 'A')
        except DNSException:
            self.logger.exception("{b} - Exception when forwarding request for address:'{addr}'".format(addr=address, b=str(self)))
            return None
        response = request.reply()
        for rdata in answers:
            ip = rdata.address
            response.add_answer(RR(address, QTYPE.A, rdata=A(ip)))
        return response

    def respond(self, request):
        """Returns response containing self.ip."""
        address = str(request.questions[0].qname)
        self.logger.log(self.parseloglevel(), "{b} - Responding to request for address:'{addr}'".format(addr=address, b=str(self)))
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
        if LOGLEVEL_KEY in json:
            self.loglevel = json[LOGLEVEL_KEY]
        else:
            self.loglevel = DEFAULT_LOGLEVEL
        return self

    def to_json(self):
        """Creates JSON object/dict representing this Behavior.

        Returns created JSON object (dict).
        """
        return {
            IP_KEY : self.ip,
            STRATEGY_KEY : self.strategy,
            ADDRESS_KEY : self.address,
            LOGLEVEL_KEY : self.loglevel }

def first_or_default(behaviors, request):
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
