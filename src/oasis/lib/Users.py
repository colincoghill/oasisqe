# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Users.py
    Handle user related operations.
"""

import hashlib
import json
import random
from logging import getLogger
import bcrypt

from oasis.lib.DB import run_sql, MC


L = getLogger("oasisqe")


def get_version():
    """ Fetch the current version of the user table.
        This will be incremented when anything in the users table is changed.
        The idea is that while the version hasn't changed, user information
        can be cached in memory.
    """
    key = "userstable-version"
    obj = MC.get(key)
    if obj is not None:
        return int(obj)

    ret = run_sql("SELECT last_value FROM users_version_seq;")
    if ret:
        ver = int(ret[0][0])

        if ver == 1:
            ver = 0
        MC.set(key, ver)
        return ver
    L.error("Error fetching version.")
    return -1


def incr_version():
    """ Increment the user table version.
    """
    key = "userstable-version"
    MC.delete(key)
    ret = run_sql("SELECT nextval('users_version_seq');")
    if ret:
        MC.set(key, int(ret[0][0]))
        return int(ret[0][0])
    L.error("Error incrementing version.")
    return -1


def get_user_record(user_id):
    """ Fetch info about the user
        returns  {'id', 'uname', 'givenname', 'lastname', 'fullname'}
    """
    # TODO: clear the cache entry when we change any of these values
    key = "user-%s-record" % (user_id,)
    obj = MC.get(key)
    if obj:
        return json.loads(obj)
    sql = """SELECT id, uname, givenname, familyname, student_id,
                    acctstatus, email, expiry, source, confirmed
                    FROM users
                    WHERE id=%s"""
    params = [user_id, ]
    ret = run_sql(sql, params)
    if ret:
        row = ret[0]
        if row[1]:
            uname = unicode(row[1], 'utf-8')
        else:
            uname = u""
        if row[2]:
            givenname = unicode(row[2], 'utf-8')
        else:
            givenname = u""
        if row[3]:
            familyname = unicode(row[3], 'utf-8')
        else:
            familyname = u""
        user_rec = {'id': user_id,
                    'uname': uname,
                    'givenname': givenname,
                    'familyname': familyname,
                    'fullname': u"%s %s" % (givenname, familyname),
                    'student_id': ret[0][4],
                    'acctstatus': ret[0][5],
                    'email': ret[0][6],
                    'expiry': ret[0][7],
                    'source': ret[0][8],
                    'confirmed': ret[0][9]}
        if ret[0][9] is True \
                or ret[0][9] == "true" \
                or ret[0][9] == "TRUE" \
                or ret[0][9] == "" \
                or ret[0][9] is None:

            user_rec['confirmed'] = True
        else:
            user_rec['confirmed'] = False

        if not user_rec['fullname']:
            if user_rec['email']:
                user_rec['fullname'] = user_rec['email']
            else:
                user_rec['fullname'] = "Unknown"
        MC.set(key, json.dumps(user_rec))
        return user_rec


def set_password(user_id, clearpass):
    """ Updates a users password. """
    hashed = bcrypt.hashpw(clearpass.encode('utf8'), bcrypt.gensalt(10))
    sql = """UPDATE "users" SET "passwd" = %s WHERE "id" = %s;"""
    params = [hashed, user_id]
    try:
        run_sql(sql, params)
    except IOError as err:
        L.error("Error settings password for user %s - %s" % (user_id, err))
        raise
    return True


def verify_password(uname, clearpass):
    """ Confirm the password is correct for the given user name.
        We first try bcrypt, if it fails we try md5 to see if they have
        an old password, and if so, upgrade the stored password to bcrypt.
    """
    sql = """SELECT "id", "passwd" FROM "users" WHERE "uname" = %s;"""
    params = [uname, ]
    ret = run_sql(sql, params)
    if not ret:
        return False
    try:
        user_id = int(ret[0][0])
    except IOError:
        L.error("Error fetching user record %s" % uname)
        raise
    stored_pw = ret[0][1]
    if len(stored_pw) > 40:  # it's not MD5
        hashed = bcrypt.hashpw(clearpass.encode('utf8'), stored_pw.encode('utf8'))
        if stored_pw == hashed:
            # All good, they matched with bcrypt
            return user_id

    # Might be an old account, check md5
    hashgen = hashlib.md5()
    hashgen.update(clearpass)
    md5hashed = hashgen.hexdigest()
    if stored_pw == md5hashed:
        # Ok, now we need to upgrade them to something more secure
        set_password(user_id, clearpass)
        L.info("Upgrading MD5 password to bcrypt for %s" % uname)
        return user_id
    return False


def create(uname, passwd, givenname, familyname, acctstatus, studentid,
           email=None, expiry=None, source="local",
           confirm_code=None, confirm=True, display_name=False):
    """ Add a user to the database. """
    L.info("Users.py:create(%s)" % uname)
    if not confirm_code:
        confirm_code = ""
    if not display_name:
        if givenname or familyname:
            display_name = "%s %s" % (givenname, familyname)
        elif email:
            display_name = email
        else:
            display_name = "Unknown"

    run_sql("""INSERT INTO users (uname, passwd, givenname, familyname,
                                  acctstatus, student_id, email, expiry,
                                  source, confirmation_code, confirmed, display_name)
               VALUES (%s, %s, %s, %s, %s, %s,
                       %s, %s, %s, %s, %s);""",
            [uname, passwd, givenname, familyname,
             acctstatus, studentid, email, expiry,
             source, confirm_code, confirm, display_name])
    incr_version()
    uid = uid_by_uname(uname)
    L.info("User created with uid %d." % uid)
    return uid


def uid_by_uname(uname):
    """ Lookup the users internal ID number given their login name. """
    key = "user-%s-unametouid" % (uname,)
    obj = MC.get(key)
    if obj is not None:
        return obj
    ret = run_sql("""SELECT id FROM "users" WHERE uname=%s;""", [uname, ])
    if ret:
        MC.set(key, ret[0][0])
        return ret[0][0]
    return None


def uid_by_email(email):
    """ Lookup the users internal ID number given their email address. """
    key = "user-%s-emailtouid" % (email,)
    obj = MC.get(key)
    if obj is not None:
        return obj
    ret = run_sql("""SELECT id FROM "users" WHERE email=%s;""", [email, ])
    if ret:
        MC.set(key, ret[0][0])
        return ret[0][0]
    return None


def find(search, limit=20):
    """ return a list of user id's that reasonably match the search term.
        Search username then student ID then surname then first name.
        Return results in that order.
    """
    ret = run_sql("""SELECT id FROM users
                        WHERE LOWER(uname) LIKE LOWER(%s)
                        OR LOWER(familyname) LIKE LOWER(%s)
                        OR LOWER(givenname) LIKE LOWER(%s)
                        OR student_id LIKE %s
                        OR LOWER(email) LIKE LOWER(%s) LIMIT %s;""",
                  [search, search, search, search, search, limit])
    res = []
    if ret:
        res = [user[0] for user in ret]
    return res


def typeahead(search, limit=20):
    """ return a list of user id's that reasonably match the search term.
        Search username then student ID then surname then first name.
        Return results in that order.
    """
    ret = run_sql("""SELECT id
                     FROM users
                     WHERE
                         LOWER(uname) LIKE LOWER(%s)
                       OR
                         LOWER(email) LIKE LOWER(%s)
                     LIMIT %s;""",
                  [search, search, limit])
    res = []
    if ret:
        res = [user[0] for user in ret]
    return res


def get_groups(user):
    """ Return a list of groups the user is a member of.  """
    assert isinstance(user, int)
    ret = run_sql("""SELECT groupid FROM usergroups WHERE userid=%s;""",
                  [user, ])
    if ret:
        groups = [int(row[0]) for row in ret]
        return groups
    L.warn("Request for unknown user or user in no groups.")
    return []


def get_courses(user_id):
    """ Return a list of the Course IDs of the courses the user is in """
    groups = get_groups(user_id)
    courses = []
    for group in groups:
        res = run_sql("""SELECT course
                         FROM groupcourses
                         WHERE groupid=%s LIMIT 1;""",
                      [group, ])
        if res:
            course_id = int(res[0][0])
            courses.append(course_id)
    return courses


def verify_confirm_code(code):
    """ Given an email confirmation code, return the user_id it was given to,
        otherwise False.
    """
    if len(code) < 5:  # don't want to match if we get an empty one
        return False
    ret = run_sql("""SELECT "id" FROM "users" WHERE confirmation_code=%s;""",
                  [code, ])
    if ret:
        return ret[0][0]
    return False


def set_confirm(uid):
    """ The user has confirmed, mark their record."""
    run_sql("""UPDATE "users" SET confirmed='TRUE' WHERE id=%s;""", [uid, ])
    incr_version()


def set_confirm_code(uid, code):
    """ Set a new code, possibly for password reset confirmation."""
    run_sql("""UPDATE "users" SET "confirmation_code" = %s WHERE "id" = %s;""",
            [code, uid])
    incr_version()


def gen_confirm_code():
    """ Generate a new email confirmation code and return it
    """

    return generate_uuid_readable(9)


def set_studentid(uid, stid):
    """ Update student ID."""
    run_sql("""UPDATE "users" SET student_id = %s WHERE "id" = %s;""", [stid, uid])
    incr_version()


def set_givenname(uid, name):
    """ Update Given Name."""
    run_sql("""UPDATE "users" SET givenname = %s WHERE "id" = %s;""", [name, uid])
    incr_version()


def set_familyname(uid, name):
    """ Update Family Name."""
    run_sql("""UPDATE "users" SET familyname = %s WHERE "id" = %s;""", [name, uid])
    incr_version()


def set_email(uid, email):
    """ Update Email."""
    run_sql("""UPDATE "users" SET email = %s WHERE "id" = %s;""", [email, uid])
    incr_version()


# Human readable symbols
def generate_uuid_readable(length=9):
    """ Create a new random uuid suitable for acting as a unique key in the db
        Use this when it's an ID a user will see as it's a bit shorter.
        Duplicates are still unlikely, but don't use this in situations where
        a duplicate might cause problems (check for them!)

        :param length: The number of characters we want in the UUID
    """
    valid = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    # 57^n possibilities - about 6 million billion options for n=9.
    # Hopefully pretty good.
    return "".join([random.choice(valid) for _ in range(length)])
