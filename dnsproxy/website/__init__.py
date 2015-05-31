# -*- coding: utf-8 -*-
"""Local website over HTTP access module.

The website allows for convenient, web-based configuration access/update,
viewing logs and starting/stopping the DNS proxy server."""

from flask import Flask, jsonify, render_template, request

from dnsproxy.config import Config
from dnsproxy.behavior import Behavior

config = Config()
app = Flask(__name__)

@app.route('/_save_port')
def save_port():
	global config
	config.dns_port = request.args.get('dnsPort', 0, type=int)
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
	
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=config.http_access_port)