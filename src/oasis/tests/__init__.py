# -*- coding: utf-8 -*-

"""testing module
"""
import sys
import os
APPDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
sys.path.append(os.path.join(APPDIR, "src"))

from oasis.lib import DB
assert DB.check_safe(), "Database not safe for tests"


def setup():
    """ Prepare database for testing.
    """
    if not DB.check_safe():
        print "Attempt to erase database with data."
        sys.exit(-1)
    with open(os.path.join(APPDIR, "deploy", "eraseexisting.sql")) as f:
        sql = f.read()
    print "Removing existing tables."
    DB.run_sql(sql)

    with open(os.path.join(APPDIR, "deploy", "emptyschema_395.sql")) as f:
        sql = f.read()

    DB.run_sql(sql)
    print "Installed v3.9.5 table structure."


def teardown():
    """
        Remove testing configuration file and otherwise clean up.
    """
    with open(os.path.join(APPDIR, "deploy", "eraseexisting.sql")) as f:
        sql = f.read()
    print "Removing tables."
    DB.run_sql(sql)
