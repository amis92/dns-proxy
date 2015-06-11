"""
Runs default empty App.
"""
from . import  App
from sys import argv

if len(argv) > 1:
    App(argv[1]).run()
else:
    App().run()