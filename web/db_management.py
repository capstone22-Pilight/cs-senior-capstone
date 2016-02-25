#!/usr/bin/env python
import os.path
import sys, imp, getopt
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from model import *

def build():
    db.create_all()
    if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
        api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    else:
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
    device1 = Device(mac='913a8d11f5c5', ipaddr='151.13.80.15', name='Device 1')
    device2 = Device(mac='45a4feaaceb3', ipaddr='159.19.22.90', name='Device 2')

    groups = [Group(id=1, name="All Lights", parent_id=None),
              Group(id=2, name="Group 2", parent_id=1),
              Group(id=3, name="Group 3", parent_id=1),
              Group(id=4, name="Group 4", parent_id=1)]

    lights = [Light(id=1, parent_id=2, name='Light 1', device_mac='913a8d11f5c5', port=1),
              Light(id=2, parent_id=2, name='Light 2', device_mac='913a8d11f5c5', port=2),
              Light(id=3, parent_id=2, name='Light 3', device_mac='913a8d11f5c5', port=3),
              Light(id=4, parent_id=3, name='Light 4', device_mac='913a8d11f5c5', port=4),
              Light(id=5, parent_id=3, name='Light 5', device_mac='45a4feaaceb3', port=1),
              Light(id=6, parent_id=3, name='Light 6', device_mac='45a4feaaceb3', port=2),
              Light(id=7, parent_id=4, name='Light 7', device_mac='45a4feaaceb3', port=3),
              Light(id=8, parent_id=4, name='Light 8', device_mac='45a4feaaceb3', port=4)]

    first_user = User(username="Pi",password="pilight")
    db.session.add(first_user)
    db.session.add(device1)
    db.session.add(device2)
    for g in groups:
        db.session.add(g)
    for l in lights:
        db.session.add(l)
    db.session.commit()

def upgrade():
    api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    print('Current database version: ' + str(v))

def migrate():
    v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    migration = SQLALCHEMY_MIGRATE_REPO + ('/versions/%03d_migration.py' % (v+1))
    tmp_module = imp.new_module('old_model')
    old_model = api.create_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    exec(old_model, tmp_module.__dict__)
    script = api.make_update_script_for_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, tmp_module.meta, db.metadata)
    open(migration, "wt").write(script)
    api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    print('New migration saved as ' + migration)
    print('Current database version: ' + str(v))


def usage():
    print "Database management script"
    print "Valid arguments:"
    print "--build to build the database for the first time"
    print "--upgrade to change the database to include new tables"
    print "--migrate to move data from one database to the new empty one"

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hbum",["help","build","upgrade","migrate"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        exit(2)
    for o,a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-b", "--build"):
            build()
        elif o in ("-u", "--upgrade"):
            upgrade()
        elif o in ("-m", "--migrate"):
            migrate()
        else:
            assert False, "Unhandled Option!"

if __name__ == "__main__":
    main(sys.argv[1:])
