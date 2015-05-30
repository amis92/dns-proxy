"""DNS proxy configuration management module."""

import behavior
import json

JSON_CONF_DEFAULT_FILE = 'dnsproxy.config'
ROOT_KEY = 'dnsProxy'
CONF_KEY = 'config'
HTTP_ACCESS_PORT_KEY = 'httpAccessPort'
DNS_PORT_KEY = 'dnsPort'
BEHAVIORS_KEY = 'behaviors'

class Config(object):
    """DNS proxy configuration class"""

    def __init__(self):
        self.default()

    def default(self):
        """Sets default values.
        """
        self.http_access_port = 8080
        self.dns_port = 53
        self.behaviors = []

    def from_json(self, json):
        """Setups Config using JSON object.

        Returns self.
        """
        config_json = json[ROOT_KEY][CONF_KEY]
        self.http_access_port = config_json[HTTP_ACCESS_PORT_KEY]
        self.dns_port = config_json[DNS_PORT_KEY]
        self.behaviors = [behavior.create(jsonBehavior) for jsonBehavior in config_json[BEHAVIORS_KEY]]
        return self

    def from_file(self, filename = JSON_CONF_DEFAULT_FILE):
        """Loads Config from file. On error default values are loaded back.

        Returns self.
        """
        try:
            with open(filename) as file:
                return self.from_json(json.load(file))
        except:
            return self.default()

    def to_json(self):
        """Creates JSON object from the Config.

        Returns JSON object.
        """
        conf_dict = {
            HTTP_ACCESS_PORT_KEY : self.http_access_port,
            DNS_PORT_KEY : self.dns_port,
            BEHAVIORS_KEY : [behavior.to_json() for behavior in self.behaviors] }
        return {ROOT_KEY : {CONF_KEY : conf_dict}}


    def to_file(self, filename = JSON_CONF_DEFAULT_FILE):
        """Saves current config to JSON-formatted config file.
        """
        with open(filename, mode = 'w') as file:
            json.dump(self.to_json(), indent = True)