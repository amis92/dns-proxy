"""DNS proxy package."""

from dnsproxy.website import WebServer
from dnsproxy.server import Server
from dnsproxy.config import Config
from threading import Thread
from sys import argv
import logging

logger = logging.getLogger('dnsproxy')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)-15s %(levelname)-8s %(name)s.%(funcName)s @ %(threadName)s : %(message)s")

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(formatter)

hdlr = logging.FileHandler('dnsapp.log')
hdlr.setFormatter(formatter)

logger.addHandler(hdlr)
logger.addHandler(consoleHandler)

class App(object):
    """DNS proxy runnable app."""

    def __init__(self, host = None):
        self.logger = logging.getLogger('dnsproxy.App')
        self.config = Config().from_file()
        self.server = Server(self.config, host)
        self.webserver = WebServer(self.config, self.server)
        #self.website_thread = Thread(name='WebServer-thread', target = self.run_website_blocking)
        self.logger.info('created')
        self.run_website_blocking()

    def run(self):
        """Starts DNS proxy server and config website server according to provided configuration.
        """
        self.logger.debug('preparing to run')
        self.server.start()
        self.website_thread.start()
        self.logger.info('server threads started')

    def run_website_blocking(self):
        self.webserver.app.run(host = '127.0.0.1', port = self.config.http_access_port)

if __name__ == '__main__':
    if len(argv) > 1:
        App(argv[1]).run()
    else:
        App().run()