#!/usr/bin/env python

from flask import Flask, render_template
app = Flask(__name__)

groups = {  
	"Group 1": ["Light 1", "Light 2", "Light 3"],
	"Group 2": ["Light 4", "Light 5", "Light 6", "Light 7"],
	"Group 3": ["Light 8", "Light 9", "Light 10", "Light 11", "Light 12", "Light 13"]
}


@app.route("/")
def index():
    return render_template('index.html', groups=groups)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
