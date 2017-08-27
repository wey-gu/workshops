#!/usr/bin/python
# run.py
from demoWSGI import app
app.run(debug=True,host='0.0.0.0',port=80)
