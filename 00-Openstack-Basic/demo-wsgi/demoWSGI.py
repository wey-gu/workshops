# -*- coding: utf-8 -*-
#!/usr/bin/python
# this is the demo WSGI.py, imagin it's NOVA-API :-p

'''
API document :
    - format: GET /hello
        It will response a self introduction string, which will hello world!
    - format: GET /doSomething
        It will call doSomethingFunction process/task, which will change the world!
'''


from flask import Flask
app = Flask(__name__)
from doSomethingLib import doSomethingFunction

@app.route("/hello")
def hello():
    # Just return a string
    return "Hello World! I am a WSGI process :-)..."

@app.route("/hello/<name>")
def helloName(name):
    # Just return a string
    return "Hello World! I am a WSGI process :-)... " + name

@app.route("/doSomething")
def doSomething():
    doSomethingFunction()
    return '''
        <br/><br/> 
        (•̀ᴗ•́)و ̑̑      Opps, you made it! <br/><br/><br/><br/> 
        ( ͡° ͜ʖ ͡°)     Did you hear about The Butterfly Effect btw.? '''