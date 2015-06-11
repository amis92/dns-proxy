"""
Script running default App from dnsproxy package.
"""
import dnsproxy
from sys import argv

if len(argv) > 1:
	dnsproxy.App(argv[1]).run()
else:
    dnsproxy.App().run()