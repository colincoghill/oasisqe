# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Interface for access to User information.
    All access to User info should come through here, and not through
    the db.Users or OaDB interface any more.

    List of users is big and accessed frequently, so we try and cache stuff
    as it's used.
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


def reload_users():
    """If interesting fields in the user table have changed, reload the info.
    """
    global USERS_VERSION
    global USERS

    newversion = Users.get_version()
    if newversion > USERS_VERSION:
        USERS_VERSION = newversion
        USERS = {}
    return


def get_user(user_id):
    """ Return a dict of various user fields.
        {'id', 'uname', 'givenname', 'familyname', 'fullname'}
    """

    reload_users()
    if user_id not in USERS:
        USERS[user_id] = Users.get_user_record(user_id)

    return USERS[user_id]


uid_by_uname = Users.uid_by_uname
uid_by_email = Users.uid_by_email

verify_pass = Users.verify_password
create = Users.create
find = Users.find
get_courses = Users.get_courses
set_password = Users.set_password

# reload_users()
