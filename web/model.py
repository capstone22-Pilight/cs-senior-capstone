from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from start import app

db = SQLAlchemy(app)
class Device(db.Model):
    mac = db.Column(db.String(12),primary_key=True)
    ipaddr = db.Column(db.String(12),index=True,unique=True) # better datatype f$
    name = db.Column(db.String(128),index=True,unique=True)

    def __getmac__(self):
        return '<MAC %r>' & (self.mac)

