#!/usr/bin/env python

import sys
import random as rand
import unicodedata,socket
from isc_dhcp_leases.iscdhcpleases import Lease, IscDhcpLeases
from flask import Flask, render_template, request, jsonify, g, session, flash, url_for, redirect, abort
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from config import SQLALCHEMY_DATABASE_URI
import model as model

engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)


app = Flask(__name__)
app.config.from_object('config')

# Login system initialization
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.secret_key = 'super_secret_key'

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
    print "The destination device: ", macs

@app.route("/")
def index():
    return render_template('index.html', groups=model.Group.query.filter_by(group_id=None))

@app.route('/buttons')
@login_required
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
    lid = request.args.get('lid')
    gid = request.args.get('gid')
    return render_template('advanced.html', lid=lid, gid=gid)

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
        if(ESP8266_check(lease.ip)):
            # We have an ESP8266 mode!
            database_check = model.Device.query.filter_by(mac=lease.ethernet).first()
            if database_check is None:
            # We have an ESP8266 AND it's not in the database!
                new_device = model.Device(mac=lease.ethernet,ipaddr=lease.ip,name="ESP8266@"+lease.ethernet)
                model.db.session.add(new_device)
                model.db.session.commit()
                additions = additions + 1
    return str(additions)

@app.route('/change_name', methods=['POST'])
def change_name():
    name = request.form['value']
    pk = request.form['pk']
    isLight = request.form['name'] == "light"
    if isLight:
        light = model.Light.query.filter_by(id=pk).first()
        light.name = name
    else:
        group = model.Group.query.filter_by(id=pk).first()
        group.name = name
    model.db.session.commit()
    return "Success!"

@app.route('/new_group', methods=['POST'])
def new_group():
    group = model.Group(name="New Group", id=None, group_id=None)
    model.db.session.add(group)
    model.db.session.commit()
    return render_template('grouplight.html', e=group)

@app.route('/delete_group', methods=['POST'])
def delete_group():
    id = request.form['id']
    old_group = model.Group.query.filter_by(id=id).first()
    for light in old_group.lights:
        light.parent_id = old_group.group.id
    for group in old_group.groups:
        group.group_id = old_group.group.id
    model.db.session.commit()
    model.Group.query.filter_by(id=id).delete()
    model.db.session.commit()
    return "Complete!"

def ESP8266_check(ipaddr):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ipaddr,9999))
    if result == 0:
        return True
    else:
        return False

def isLight(o):
    return isinstance(o, model.Light)

@login_manager.user_loader
def load_user(id):
    return model.User.query.get(int(id))

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    registered_user = model.User.query.filter_by(username=username,password=password).first()
    if registered_user is None:
        flash('Invalid Credientals','error')
        return redirect(url_for('login'))
    login_user(registered_user)
    flash('Logged in')
    g.user=registered_user
    return redirect(request.args.get('next') or url_for('index'))

@app.route("/logout")
def logout():
    logout_user()
    g.user = None
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.jinja_env.globals.update(isLight=isLight)
    app.jinja_env.globals.update(enumerate=enumerate)
    app.run(host='0.0.0.0', port=8080, debug=True)
