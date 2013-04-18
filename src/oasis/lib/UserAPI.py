# -*- coding: utf-8 -*-

""" Interface for access to User information.
    All access to User info should come through here, and not through
    the db.Users or OaDB interface any more.

    List of users is big and accessed frequently, so we try and cache stuff as it's used.
"""

# Get the latest version of the user info
# We can cache information until this changes,
# then we
# need to flush and reread it from the Db layer
# Something more fine-grained would be better longer term,
# but this will do nicely for now.
# We bump the version if any of  user    uname, firstname, lastname change
from . import Users

USERS_VERSION = -1

# We store user  [id] = { id, uname, givenname, familyname}
USERS = {}


def reloadUsersIfNeeded():
    """If interesting fields in the user table have changed, reload the info.
    """
    global USERS_VERSION
    global USERS

    newversion = Users.getVersion()
    if newversion > USERS_VERSION:
        USERS_VERSION = newversion
        USERS = {}
    return


def getUser(user_id):
    """ Return a dict of various user fields.
        {'id', 'uname', 'givenname', 'familyname', 'fullname'}
    """

    reloadUsersIfNeeded()
    if not user_id in USERS:
        USERS[user_id] = Users.getUserRecord(user_id)

    return USERS[user_id]


getUidByUname = Users.getUidByUname
verifyPass = Users.verifyPass
create = Users.create
find = Users.find
getCourses = Users.getCourses
setPassword = Users.setPassword

reloadUsersIfNeeded()
