# -*- coding: utf-8 -*-
"""Local website over HTTP access module.

The website allows for convenient, web-based configuration access/update,
viewing logs and starting/stopping the DNS proxy server."""

from flask import Flask, jsonify, render_template, request

class Config:
	def __init__(self, ip, strategy, address):
		self.ip = ip
		self.strategy = strategy
		self.address = address

wwwPort = 5002
dnsPort = 53
app = Flask(__name__)
items = []

@app.route('/_save_port')
def save_port():
	global dnsPort
	dnsPort = request.args.get('dnsPort', 0, type=int)
	return jsonify(result = True)
	
@app.route('/_load_port')
def load_port():
	port = dict(dnsPort = dnsPort)
	return jsonify(results = port)
	
@app.route('/_load_configuration')
def load_configuration():
	print "load"
	return jsonify(results = items)

@app.route('/_delete_configuration')
def delete_configuration():
	id = request.args.get('id', 0, type=int)
	items.pop(id)
	return jsonify(result = True)
	
@app.route('/_save_configuration')
def save_configuration():
	ip = request.args.get('ip')
	strategy = request.args.get('strategy')
	address = request.args.get('address')
	items.append(dict(ip = ip, strategy = strategy, address=address))
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
    app.run(host='127.0.0.1', port=wwwPort)