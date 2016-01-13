#!/usr/bin/env python
import os.path
import sys, imp, getopt
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from model import db

def build():
    db.create_all()
    if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
        api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
    else:
        api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))

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
