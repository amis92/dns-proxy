"""DNS proxy package."""

from dnsproxy.website import WebServer
from dnsproxy.server import Server
from dnsproxy.config import Config
from threading import Thread

class App(object):
    """DNS proxy runnable app."""

    def __init__(self):
        self.config = Config().from_file()
        self.server = Server(self.config)
        self.webserver = WebServer(self.config, self.server)
        self.website_thread = Thread(name='WebServer website thread', target = self.run_website_blocking)

    def run(self):
        """Starts DNS proxy server and config website server according to provided configuration.
        """
        self.server.start()
        self.website_thread.start()

    def run_website_blocking(self):
        self.webserver.app.run(host = '127.0.0.1', port = self.config.http_access_port)

if __name__ == '__main__':
    App().run()