#!/usr/bin/env python

import random as rand
from flask import Flask, render_template
app = Flask(__name__)

class Light(object):
    index = 0
    def __init__(self, mac=None, port=None, name=None):
        Light.index += 1

        if mac is None:
            self.mac = ":".join([hex(rand.randint(0, 255))[-2:] for n in xrange(6)])
        else:
            self.mac = mac

        if port is None:
            self.port = rand.randint(1, 4)
        else:
            self.port = port

        if name is None:
            self.name = "Light {}".format(Light.index)
        else:
            self.name = name

    def __repr__(self):
        return "Light({}, {}, {})".format(self.name, self.mac, self.port)

class Group(object):
    index = 0
    def __init__(self, name=None):
        Group.index += 1
        self.gid = Group.index
        self.members = []
        if name is None:
            self.name = "Group {}".format(Group.index)
        else:
            self.name = name

    def __repr__(self):
        return "Group({})".format(", ".join(map(str, self.members)))

    def append(self, light):
        self.members.append(light)

# Initialize some dummy groups to start with
groups = [Group("House")]
for gi in xrange(3):
    g = Group()
    for li in xrange(rand.randint(1, 5)):
        g.append(Light())
    groups[0].append(g)

print groups

@app.route("/")
def index():
    return render_template('index.html', groups=groups)

@app.route("/advanced")
def advanced():
    return render_template('index.html', groups=groups)

def isLight(o):
    return isinstance(o, Light)

if __name__ == "__main__":
    app.jinja_env.globals.update(isLight=isLight)
    app.run(host='0.0.0.0', port=8080, debug=True)
