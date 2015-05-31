"""DNS proxy package."""

from dnsproxy.website import app as website_app, config as website_config
from dnsproxy.config import Config

proxy_config = Config().from_file()
website_config = proxy_config


class App(object):
    """DNS proxy runnable app."""

    def run(self):
        """
        Starts DNS proxy server and config website server according to provided configuration.
        """
        # TODO run DNS proxy server
        website_app.run(host = '127.0.0.1', port = proxy_config.http_access_port)

if __name__ == '__main__':
    App().run()