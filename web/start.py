#!/usr/bin/env python

import random as rand
import unicodedata,socket
from isc_dhcp_leases.iscdhcpleases import Lease, IscDhcpLeases
from flask import Flask, render_template, request, jsonify
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')

import model

class Light(object):
    index = 0
    def __init__(self, mac=None, port=None, name=None):
        Light.index += 1

        if mac is None:
            self.mac = ":".join(["{:x}".format(rand.randint(0, 255)).zfill(2) for n in xrange(6)])
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

# The light's current state, move this to the class when ready
global CURR_STATE
CURR_STATE = '0000'

AVAILABLE_COMMANDS = {
    '1 ON': '11000',
    '2 ON': '10100',
    '3 ON': '10010',
    '4 ON': '10001',
    '1 OFF': '00111',
    '2 OFF': '01011',
    '3 OFF': '01101',
    '4 OFF': '01110',
}
# This function should also be a member of a lights class too
def enlighten(cmd,mac):
    new_state = ""
    if cmd[0] == '0':
        for count in range(1,5):
            if cmd[count] == '0':
                new_state+='0'
            else:
                new_state+=CURR_STATE[count-1]
    else:
        for count in range(1,5):
            if cmd[count] == '1':
                new_state+='1'
            else:
                new_state+=CURR_STATE[count-1]

    global CURR_STATE
    CURR_STATE = new_state
    # send the new CURR_STATE to TCP here
    print "The current global state: ", CURR_STATE
    print "The destination device: ", mac

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

@app.route('/buttons')
def buttons():
    return render_template('buttons.html', commands=AVAILABLE_COMMANDS)

@app.route('/buttons_proc',methods=['POST'])
def command(cmd=None):
    light_command = request.json['command']
    mac = request.json['mac']
    unicodedata.normalize('NFKD',light_command).encode('ascii','ignore')
    unicodedata.normalize('NFKD',mac).encode('ascii','ignore')
    enlighten(light_command,mac)
    return light_command+"@"+mac, 200, {'Content-Type': 'text/plain'}

@app.route("/advanced")
def advanced():
    return render_template('index.html', groups=groups)

@app.route("/devices")
def devices():
    all_devices = model.Device.query.all()
    return render_template('devices.html',devices=all_devices)

@app.route("/devices/search", methods=['POST'])
def devices_search():

    # Get all DHCP leases currently given out
    leases = IscDhcpLeases('/var/lib/dhcp/dhcpd.leases')
    leases = leases.get()

    # No DHCP leases at all, the server is not operating
    if not leases:
        return "NODHCP"

    additions = 0
    # For each lease, first see if it's an ESP8266
    for iteration,lease in enumerate(leases):
        if(ESP8266_check(lease.ip)==True):
            # We have an ESP8266 module!
            database_check = model.Device.query.filter_by(mac=lease.ethernet).first()
            if database_check is None:
            # We have an ESP8266 AND it's not in the database!
                new_device = model.Device(mac=lease.ethernet,ipaddr=lease.ip,name="ESP8266@"+lease.ethernet)
                model.db.session.add(new_device)
                model.db.session.commit()
                additions = additions + 1
    return str(additions)

def ESP8266_check(ipaddr):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ipaddr,9999))
    if result == 0:
        return True
    else:
        return False

def isLight(o):
    return isinstance(o, Light)

if __name__ == "__main__":
    app.jinja_env.globals.update(isLight=isLight)
    app.run(host='0.0.0.0', port=8080, debug=True)
