"""DNS proxy package."""

from dnsproxy.website import WebServer
from dnsproxy.server import Server
from dnsproxy.config import Config
from threading import Thread
import logging

# below config is to be removed
logging.basicConfig()

logger = logging.getLogger('dnsproxy')

# as well as those
logger.setLevel(logging.DEBUG)
logger.info('dnsproxy init')

class App(object):
    """DNS proxy runnable app."""

    def __init__(self):
        self.logger = logging.getLogger('dnsproxy.App')
        self.config = Config().from_file()
        self.server = Server(self.config)
        self.webserver = WebServer(self.config, self.server)
        self.website_thread = Thread(name='WebServer website thread', target = self.run_website_blocking)
        self.logger.info('created')

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
    App().run()