#!/usr/bin/python

from flask import Flask, render_template , url_for , request
from requestMiniECM import heatInstantiation
app = Flask(__name__)

@app.route('/', methods = ['GET', 'POST'])
def ochestrationDemo():
    if request.method == 'GET':
        return render_template('ochestrator.html')

@app.route('/instantiation', methods = ['POST'])
def instantiation():
    stackName = request.form['stack_name_form']
    netID = request.form['net_id_form']
    templateURL = request.form['template_url_form']
    # return stackName + " " + netID + " " + templateURL
    return heatInstantiation(stackName,netID,templateURL)