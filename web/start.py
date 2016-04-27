#!/usr/bin/env python

from datetime import datetime, timedelta
import json
import random as rand
import sys
import getopt
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

from gen_query import gen_query
from qtime import qtime

# Set default flags
debug = 0
rule_eval_period = 5
time_warp_enabled = False

time_offset = timedelta()

engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

ast = Astral()
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
    return render_template('index.html', root_group=model.Group.query.filter_by(parent_id=None).first())

@app.route("/settings")
def settings():
    model.Setting.query.filter_by(name='city').first().value
    settings = {}
    for s in model.Setting.query.all():
        settings[s.name] = s.value

    for region in geo:
        if settings['city'] in getattr(geo, region).locations:
            break
    return render_template('settings.html', regions=sorted(geo), region=region, settings=settings)

def str2bool(st):
    try:
        return ['false', 'true'].index(st.lower())
    except (ValueError, AttributeError):
        raise ValueError('no Valid Conversion Possible')

@app.route('/enlighten',methods=['POST'])
def enlighten():
    light_type = request.form['type']
    action = request.form['state']
    result = "OK"
    if light_type == 'group':
        group = model.Group.query.filter_by(id=request.form['group']).first()
        group.status = int(str2bool(action))
        print group.groups, " with ", len(group.groups) , " children"
        for item in xrange(0,len(group.lights)):
            result = send_command(group.lights[item],str2bool(action))
    if light_type == 'light':
        light = model.Light.query.filter_by(id=request.form['light']).first()
        print "Light at ", light.device_mac
	result = send_command(light,str2bool(action))
    return result

def send_command(light, action):
    ip = str(light.device.ipaddr)
    tcp_port = 9999
    action = int(not action) 
    command = ""
    for lights in range(0,4):
        if light.device.lights[lights].port == light.port:
            #print "SEND TO ", light.port
            command += str(str(action))
            lightUpdate = model.Light.query.filter_by(id=light.device.lights[lights].id).first()
            lightUpdate.status = int(not action)
            model.db.session.commit()
        elif light.device.lights[lights].status is None:
            command += '1'
        else:
            command += str(int(not light.device.lights[lights].status))
    #print command
    if not debug:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((ip,tcp_port))
        sock.send(command)
    return "OK"

@app.route("/advanced")
def advanced():
    lid = request.args.get('lid')
    gid = request.args.get('gid')
    if lid != None:
        light = model.Light.query.filter_by(id=int(lid)).first()
        name = light.name
        querydata = light.querydata
    else:
        group = model.Group.query.filter_by(id=int(gid)).first()
        name = group.name
        querydata = group.querydata
    if(querydata != None):
        querydata = json.loads(querydata)
    else:
        querydata = {
            "hierarchy": "or",
            "time": {
                "on": {
                    "time": "",
                },
                "off": {
                    "time": ""
                },
            },
            "range": {
                "on": {},
                "off": {}
            }
        }
    return render_template('advanced.html', lid=lid, gid=gid, name=name, querydata=querydata)

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

def add_device(mac, ipaddr, name):
    # Create the device
    new_device = model.Device(mac=mac,ipaddr=ipaddr,name=name)
    model.db.session.add(new_device)
    model.db.session.commit()

    # Create a group
    new_group = model.Group(parent_id=1, name="Group")
    model.db.session.add(new_group)
    model.db.session.commit()
    new_group.name = "Group {}".format(new_group.id)
    model.db.session.commit()

    # Create the lights
    for i in xrange(4):
        new_light = model.Light(parent_id=new_group.id, name="Light", device_mac=mac, port=i)
        model.db.session.add(new_light)
        model.db.session.commit()
        new_light.name = "Light {}".format(new_light.id)
        model.db.session.commit()

@app.route('/change_name', methods=['POST'])
def change_name():
    name = request.form['value']
    pk = request.form['pk']
    if request.form['name'] == "light":
        light = model.Light.query.filter_by(id=pk).first()
        light.name = name
    elif request.form['name'] == "group":
        group = model.Group.query.filter_by(id=pk).first()
        group.name = name
    elif request.form['name'] == "device":
        device = model.Device.query.filter_by(mac=pk).first()
        device.name = name
    else:
        print "invalid name"
        return "ERROR"
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
    selected_city = model.Setting.query.filter_by(name='city').first().value
    city_string = ""
    for city in sorted(getattr(geo, region).locations):
        if(city == selected_city):
            city_string += "<option selected>" + city + "</option>"
        else:
            city_string += "<option>" + city + "</option>"
    return city_string

@app.route('/save_setting', methods=['POST'])
def save_setting():
    name = request.form['name']
    value = request.form['value']
    model.Setting.query.filter_by(name=name).first().value = value
    model.db.session.commit()
    return name + "," + value

@app.route('/advanced_getquery', methods=['POST'])
def advanced_getquery():
    d = request.json
    querydata = json.dumps(d['querydata'])
    query = gen_query(querydata)
    return json.dumps(query), 200, {'ContentType': 'application/json'}

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

# Adds an hour to the current time_offset; this function should be scheduled to
# run once every second, making a day happen in 24 seconds.
def time_warp():
    global time_offset
    time_offset += timedelta(hours=1)

# Evaluate all light/group queries and send updates to client nodes
def run_queries():
    print "Running all queries"

    # Set up Astral
    city_name = model.Setting.query.filter_by(name='city').first().value
    city = ast[city_name]
    now = qtime(datetime.now() + time_offset)
    sun = city.sun(date=now.time, local=True)
    sunrise = sun['sunrise'].replace(tzinfo=None)
    sunset = sun['sunset'].replace(tzinfo=None)

    # Evaluate groups and lights in top-down order since parents need to be
    # evaluated first in case their state is referenced by their children.
    root = model.Group.query.filter_by(parent_id=None).first()
    eval_order = traverse_tree(root)
    for e in eval_order:

        # Generate query
        if e.querydata == None or e.querydata == "":
            query = "parent"
        else:
            query = gen_query(e.querydata)

        # Don't evaluate the query if the light is under manual control
        if query == "manual":
            print "'{}' is under manual control; skipping".format(e.name)
            continue # Don't do anything if the light is under manual control

        # Set variables for query evaluation, such as "time", "sunset", etc.
        inputs = {
            "qtime": qtime, # Pass the qtime class for evaluation
            "time": now,
            "dow": now.time.weekday(),
            "year": now.time.year,
            "month": now.time.month,
            "day": now.time.day,
            "sunrise": sunrise,
            "sunset": sunset
        }

        # Also set the parent variable unless this is the root group, which has no parent
        if e.parent != None:
            inputs["parent"] = e.parent.status
        else:
            inputs["parent"] = False

        # Get the result of the previous query
        previous_rule_state = e.rulestatus

        # Evaluate query using no global vars and with local vars from above
        try:
            current_rule_state = eval(query, {}, inputs)
        except StandardError as exception:
            print "'{}' has a bad query ({}: {}); skipping".format(e.name, exception.__class__.__name__, exception)
            continue # Don't do anything if the light has a bad query

        # Print query info for debugging
        if debug >= 2:
            if isinstance(e, model.Light):
                print "Light '{}'".format(e.name)
            else:
                print "Group '{}'".format(e.name)
            print "Query:\t{}".format(query)
            print "Previous rule:\t{}".format(previous_rule_state)
            print "Current rule:\t{}".format(current_rule_state)
            print "Current state:\t{}".format(bool(e.status))

        # For an explanation of this logic, see here:
        # https://github.com/rettigs/cs-senior-capstone/issues/27#issuecomment-194592403
        if bool(e.status) == previous_rule_state and bool(e.status) != current_rule_state:
            if debug >= 2:
                print "New state:\t{}".format(current_rule_state)
            current_rule_state_int = 1 if current_rule_state else 0

            # Send update to light
            if isinstance(e, model.Light):
                send_command(e, current_rule_state_int)

            # Update current state in database
            if isinstance(e, model.Light):
                e.status = current_rule_state_int
            else:
                e.status = current_rule_state
        else:
            if debug >= 2:
                print "Not changing state"

        # Update the current rule state in the database so it can be used as
        # the previous rule state the next time this function runs
        e.rulestatus = current_rule_state

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

def init_debug():
    add_device("913a8d11f5c5", "151.13.80.15", "Device 1")
    add_device("45a4feaaceb3", "159.19.22.90", "Device 2")

def show_help():
    '''Prints command line usage help.'''
    helpLines = [
        ("-h, --help", "Show this help"),
        ("-d, --debug", "Run in debug mode; show debug info"),
        ("-p SECONDS, --rule-eval-period SECONDS", "Set how often to evaluate rules"),
        ("-t, --time-warp", "Simulate fast time; a day completes in 24 seconds")
    ]
    for line in helpLines:
        print "{:<32}\t{}".format(*line)

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdp:t", ["help", "debug", "rule-eval-period=", "time-warp"])
    except getopt.GetoptError as err:
        print str(err)
        exit(2)
    for o, a in opts:
        if o in ("-d", "--debug"):
            debug += 1
        elif o in ("-p", "--rule-eval-period"):
            rule_eval_period = int(a)
        elif o in ("-t", "--time-warp"):
            time_warp_enabled = True
        else:
            show_help()
            sys.exit(0)

    if(debug and len(model.Device.query.all()) == 0):
        init_debug()

    # Schedule queries to run periodically
    schedule.every(rule_eval_period).seconds.do(run_queries)

    # Schedule a time warp to simulate time running more quickly
    if time_warp_enabled:
        schedule.every(1).seconds.do(time_warp)

    # Spin off the scheduler thread
    t = Thread(target=run_schedule)
    t.daemon = True # Makes the thread stop when the parent does
    t.start()
    app.jinja_env.globals.update(isLight=isLight)
    app.jinja_env.globals.update(enumerate=enumerate)
    app.run(host='0.0.0.0', port=8080, debug=debug)
