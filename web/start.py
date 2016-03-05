#!/usr/bin/env python

import datetime
import json
import random as rand
import sys
from threading import Thread
import time

import unicodedata,socket
from isc_dhcp_leases.iscdhcpleases import Lease, IscDhcpLeases
from flask import Flask, render_template, request, jsonify, g, session, flash, url_for, redirect, abort
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from config import SQLALCHEMY_DATABASE_URI
from astral import Astral
import model as model
import schedule

engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

a = Astral()
geo = Astral().geocoder

app = Flask(__name__)
app.config.from_object('config')

# Login system initialization
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.secret_key = 'super_secret_key'

@app.route("/")
def index():
    return render_template('index.html', groups=model.Group.query.filter_by(parent_id=None), lights=model.Light.query.filter_by(parent_id=None))

@app.route("/settings")
def settings():
    return render_template('settings.html', geo=sorted(geo))

@app.route('/enlighten',methods=['POST'])
def enlighten():
    light_type = request.form['type']
    action = request.form['state']
    if light_type == 'group':
        group = model.Group.query.filter_by(id=request.form['group']).first()
        print group.groups, " with ", len(group.groups) , " children"
        for item in xrange(0,len(group.lights)):
            result = send_command(group.lights[item],action)
    if light_type == 'light':
        light = model.Light.query.filter_by(id=request.form['light']).first()
        print "Light at ", light.device_mac
        result = send_command(light,action)
    return result

def send_command(light, action):
    print "Sending command to ", light.device.ipaddr, " on ", light.port, " turning it to ", action
    ip = str(light.device.ipaddr)
    tcp_port = 9999
    command = ""
    for lights in range(0,4):
        print light.device.lights[lights].status
        if light.device.lights[lights].port == light.port:
            print "SEND TO ", light.port
            command += str(action)
            lightUpdate = model.Light.query.filter_by(id=light.device.lights[lights].id).first()
            lightUpdate.status = action
            model.db.session.commit()
        elif light.device.lights[lights].status is None:
            command += '0'
        else:
            command += str(light.device.lights[lights].status)
    print command
    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #result = sock.connect_ex((ip,tcp_port))
    #sock.send(command)
    return "OK"

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
                add_device(lease.ethernet,lease.ip,"ESP8266@"+lease.ethernet)
                additions = additions + 1
    return str(additions)

def add_device(new_mac,new_ipaddr,new_name):
    new_device = model.Device(mac=new_mac,ipaddr=new_ipaddr,name=new_name)
    model.db.session.add(new_device)
    new_group = model.Group(name = "Group for " + new_mac, parent_id=1)
    model.db.session.add(new_group)
    model.db.session.commit()
    for i in range(1,5):
        new_light = model.Light(parent_id = new_group.id, name="Light " + str(i) + " on " + new_mac, device_mac = new_mac, port=i)
        model.db.session.add(new_light)
    model.db.session.commit()

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
    group = model.Group(name="New Group", id=None, parent_id=model.Group.query.filter_by(parent_id=None).first().id)
    model.db.session.add(group)
    model.db.session.commit()
    return render_template('grouplight.html', e=group)

@app.route('/change_parent', methods=['POST'])
def change_parent():
    parent_id = request.form['parent_id'];
    if parent_id == 'undefined':
        parent_id = None;
    if 'gid' in request.form:
        group = model.Group.query.filter_by(id=request.form['gid']).first()
        group.parent_id = parent_id;
    else:
        light = model.Light.query.filter_by(id=request.form['lid']).first()
        light.parent_id = parent_id;
    model.db.session.commit()
    return "Complete!"

@app.route('/delete_group', methods=['POST'])
def delete_group():
    id = request.form['id']
    old_group = model.Group.query.filter_by(id=id).first()
    for light in old_group.lights:
        light.parent_id = old_group.parent_id
    for group in old_group.groups:
        group.parent_id = old_group.parent_id
    model.db.session.commit()
    model.Group.query.filter_by(id=id).delete()
    model.db.session.commit()
    return "Complete!"

@app.route('/select_region', methods=['POST'])
def select_region():
    region = request.form['region']
    location_string = ""
    for location in sorted(getattr(geo, region).locations):
        location_string += "<option>" + location + "</option>"
    return location_string

@app.route('/select_city', methods=['POST'])
def select_city():
    city = request.form['city']
    #DO THINGS WITH CITY HERE
    return city

@app.route('/advanced_update', methods=['POST'])
def advanced_update():
    d = request.json
    if 'lid' in d: # We are updating a light
        grouplight = model.Light.query.filter_by(id=int(d['lid'])).first()
    else: # We are updating a group
        grouplight = model.Group.query.filter_by(id=int(d['gid'])).first()
    grouplight.querydata = json.dumps(d['querydata'])
    model.db.session.commit()
    return 'Update successful'

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

# Given a query data structure in JSON format, returns a query in the form of a boolean expression.
def gen_query(data):

    # If the query isn't valid JSON (or is empty), just return a "False" query.
    try:
        data = json.loads(data)
    except TypeError:
        return "False"

    # If a custom query is defined, just return that.
    custom = data.get('custom_query', "")
    if custom != "":
        return custom
    else:
        query = "time > {} and time < {}".format(data['time']['on'],
                                                 data['time']['off'])

        dayqueries = []
        if 'dow' in data:
            dayqueries.append(" or ".join(["dow == {}".format(d) for d in data['dow']]))
        if 'dom' in data:
            if 'off' in data['dom']:
                dayqueries.append("(dom >= {} and dom <= {})".format(data['dom']['on'],
                                                                   data['dom']['off']))
            else: # Only work for the 'on' day
                dayqueries.append("dom == {}".format(data['dom']['on']))
        if 'doy' in data:
            dayqueries.append("(" + " and ".join(["{} == {}".format(k, v) for k, v in data['doy'].iteritems()]) + ")")
        if len(dayqueries) > 0:
            query = "({}) and ({})".format(query, " or ".join(dayqueries))

        if data['hierarchy'] == 'manual':
            query = "manual"
        elif data['hierarchy'] == 'parent':
            query = "parent"
        elif data['hierarchy'] == 'or':
            query = "({}) or parent".format(query)
        elif data['hierarchy'] == 'and':
            query = "({}) and parent".format(query)
        # If the type is 'own', no changes are made to the query.
        return query

# Evaluate all light/group queries and send updates to client nodes
def run_queries():
    print "Running all queries"

    # Set up Astral
    city_name = 'Seattle'
    city = a[city_name]
    now = datetime.datetime.now()
    sun = city.sun(date=now, local=True)
    sunrise = sun['sunrise']
    sunset = sun['sunset']
    now = now.replace(tzinfo=sunrise.tzinfo)

    # Evaluate groups and lights in top-down order since parents need to be
    # evaluated first in case their state is referenced by their children.
    root = model.Group.query.filter_by(parent_id=None).first()
    eval_order = traverse_tree(root)
    for e in eval_order:
        # Set variables for query evaluation, such as "time", "sunset", etc.
        inputs = {
            "time": now,
            "sunrise": sunrise,
            "sunset": sunset
        }
        # Also set the parent variable unless this is the root group, which has no parent
        if e.parent != None:
            inputs["parent"] = e.parent.status

        # Evaluate query using no global vars and with local vars from above
        query = gen_query(e.querydata)
        state = eval(query, {}, inputs)
        intstate = 1 if state else 0

        if isinstance(e, model.Light):
            print "Light '{}' on? {}. Query: '{}'".format(e.name, state, query)

            # Send update to light
            send_command(e, intstate)
        else:
            print "Group '{}' on? {}. Query: '{}'".format(e.name, state, query)

        # Update state in database for website to read
        e.status = intstate
        model.db.session.commit()

# Given a root group/light, returns a list of all tree elements in the order
# they should be evaluated, i.e. top down.
def traverse_tree(root):
    sublist = [root]
    # If the given node is a light, return a list with just itself.
    if isinstance(root, model.Light):
        return sublist
    else:
        sublist.extend(list(root.lights))
        for g in root.groups:
            sublist.extend(traverse_tree(g))
        return sublist

# Thread for schedule module to run scheduled tasks
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Spin off a scheduler thread to run the queries periodically
    schedule.every(5).seconds.do(run_queries)
    t = Thread(target=run_schedule)
    t.daemon = True # Makes the thread stop when the parent does
    t.start()

    app.jinja_env.globals.update(isLight=isLight)
    app.jinja_env.globals.update(enumerate=enumerate)
    app.run(host='0.0.0.0', port=8080, debug=True)
