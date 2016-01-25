from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from start import app

db = SQLAlchemy(app)
class Device(db.Model):
    mac = db.Column(db.String(12),primary_key=True)
    ipaddr = db.Column(db.String(12),index=True,unique=True) # better datatype for IP address? Consult Sean and Malcom
    name = db.Column(db.String(128),index=True,unique=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True , index=True)
    password = db.Column(db.String(10))
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)
