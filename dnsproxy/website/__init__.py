# -*- coding: utf-8 -*-
"""Local website over HTTP access module.

The website allows for convenient, web-based configuration access/update,
viewing logs and starting/stopping the DNS proxy server."""

from flask import Flask, jsonify, render_template, request

from dnsproxy.config import Config
from dnsproxy.behavior import Behavior
import logging

logger = logging.getLogger('dnsproxy.website')

class WebServer(object):
    def __init__(self, config = None, proxyserver = None):
        self.logger = logging.getLogger('dnsproxy.website.WebServer')
        self.logger.debug('server creation started')
        if not config:
            config = Config()
        self.config = config
        self.proxyserver = proxyserver
        app = Flask(__name__)
        self.app = app

        @app.route('/_start_proxy')
        def start_proxy():
            proxyserver.start()
            return jsonify(isAlive=proxyserver.is_alive())

        @app.route('/_stop_proxy')
        def stop_proxy():
            proxyserver.stop()
            return jsonify(isAlive=proxyserver.is_alive())

        @app.route('/_proxy_status')
        def is_proxy_alive():
            return jsonify(isAlive=proxyserver.is_alive())

        @app.route('/_save_port')
        def save_port():
            config.dns_port = request.args.get('dnsPort', 0, type=int)
            self.logger.debug('saved DNS port {port}', port = config.dns_port)
            config.to_file()
            return jsonify(result = True)

        @app.route('/_load_port')
        def load_port():
            response = jsonify(results = dict(dnsPort = config.dns_port))
            return response

        @app.route('/_load_configuration')
        def load_configuration():
            print 'load'
            return jsonify(results = [b.to_json() for b in config.behaviors])

        @app.route('/_delete_configuration')
        def delete_configuration():
            id = request.args.get('id', 0, type=int)
            config.behaviors.pop(id)
            config.to_file()
            return jsonify(result = True)

        @app.route('/_save_configuration')
        def save_configuration():
            ip = request.args.get('ip')
            strategy = request.args.get('strategy')
            address = request.args.get('address')
            new_behavior = Behavior(address, strategy, ip)
            config.behaviors.append(new_behavior)
            config.to_file()
            return jsonify(result = True)

        @app.route('/')
        def index():
            return render_template('index.html')

        @app.route('/index.html')
        def index_html():
            return render_template('index.html')

        @app.route('/logs.html')
        def logs():
            return render_template('logs.html')

        self.logger.info('server created')

if __name__ == '__main__':
    app = WebServer().app
    app.run(host='127.0.0.1', port=config.http_access_port)