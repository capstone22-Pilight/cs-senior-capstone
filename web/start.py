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

debug = False

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
    override = request.form['override']
    override_time = time.strptime(model.Setting.query.filter_by(name = "overridetime").first().value, "%H:%M")
    futureTime = datetime.now() + timedelta(minutes=((override_time.tm_hour * 60)+override_time.tm_min))
    result = "OK"
    if light_type == 'group':
        group = model.Group.query.filter_by(id=request.form['group']).first()
        group.override = futureTime.strftime("%s")
        group.status = int(str2bool(action))
        print group.groups, " with ", len(group.groups) , " children"
        for item in xrange(0,len(group.lights)):
            if override == "True":
                lightUpdate = model.Light.query.filter_by(id=group.lights[item].id).first()
                lightUpdate.override = futureTime.strftime("%s")
                model.db.session.add(lightUpdate)
                model.db.session.commit()
            result = send_command(group.lights[item],str2bool(action))
    if light_type == 'light':
        light = model.Light.query.filter_by(id=request.form['light']).first()
        print "Light at ", light.device_mac
        if override == "True":
            light.override = futureTime.strftime("%s")
            model.db.session.add(light)
            model.db.session.commit()
	result = send_command(light,str2bool(action))
    return result

def send_command(light, action):
    #print "Sending command to ", light.device.ipaddr, " on ", light.port, " turning it to ", action
    ip = str(light.device.ipaddr)
    tcp_port = 9999
    command = ""
    for lights in range(0,4):
        #print light.device.lights[lights].status
        if light.device.lights[lights].port == light.port:
            #print "SEND TO ", light.port
            command += str(str(action))
            lightUpdate = model.Light.query.filter_by(id=light.device.lights[lights].id).first()
            lightUpdate.status = int(action)
            model.db.session.commit()
        elif light.device.lights[lights].status is None:
            command += '0'
        else:
            command += str(light.device.lights[lights].status)
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

# Evaluate all light/group queries and send updates to client nodes
def run_queries():
    print "Running all queries"

    # Set up Astral
    city_name = model.Setting.query.filter_by(name='city').first().value
    city = ast[city_name]
    now = qtime(datetime.now())
    sun = city.sun(date=now.time, local=True)
    sunrise = sun['sunrise'].replace(tzinfo=None)
    sunset = sun['sunset'].replace(tzinfo=None)

    # Evaluate groups and lights in top-down order since parents need to be
    # evaluated first in case their state is referenced by their children.
    root = model.Group.query.filter_by(parent_id=None).first()
    eval_order = traverse_tree(root)
    for e in eval_order:
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

        # Evaluate query using no global vars and with local vars from above
        if e.querydata == None or e.querydata == "":
            query = "parent"
        else:
            query = gen_query(e.querydata)

        if query == "manual":
            print "'{}' is under manual control; skipping".format(e.name)
            continue # Don't do anything if the light is under manual control

        try:
            state = eval(query, {}, inputs)
        except StandardError as exception:
            print "'{}' has a bad query ({}: {}); skipping".format(e.name, exception.__class__.__name__, exception)
            continue # Don't do anything if the light has a bad query

        intstate = 1 if state else 0

        if isinstance(e, model.Light):
            print "Light '{}' on? {}. Query: '{}'".format(e.name, state, query)
            timeNow = datetime.now().strftime("%s")
            if int(e.override) > int(timeNow):
                print "Not running query. Override in place until " + str(e.override)
            else:
                # Send update to light
                send_command(e, intstate)

                # Update state in database for website to read
                e.status = intstate
                model.db.session.commit()
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

def init_debug():
    add_device("913a8d11f5c5", "151.13.80.15", "Device 1")
    add_device("45a4feaaceb3", "159.19.22.90", "Device 2")

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hd",["help", "debug"])
    except getopt.GetoptError as err:
        print str(err)
        exit(2)
    for o,a in opts:
        if o in ("-h", "--help"):
            print "--debug to run in debug mode"
            sys.exit(0)
        elif o in ("-d", "--debug"):
            debug = True
        else:
            assert False, "Unhandled Option!"

    if(debug and len(model.Device.query.all()) == 0):
        init_debug()

    # Spin off a scheduler thread to run the queries periodically
    schedule.every(5 if debug else 60).seconds.do(run_queries)
    t = Thread(target=run_schedule)
    t.daemon = True # Makes the thread stop when the parent does
    t.start()
    app.jinja_env.globals.update(isLight=isLight)
    app.jinja_env.globals.update(enumerate=enumerate)
    app.run(host='0.0.0.0', port=8080, debug=debug)
