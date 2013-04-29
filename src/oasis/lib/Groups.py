# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Groups.py
    Handle group related operations.
"""

import datetime
from oasis.lib.OaDB import run_sql, dbpool
from logging import log, WARN, INFO


def create(name, description, owner, grouptype, startdate=None, enddate=None):
    """ Add a group to the database. """
    conn = dbpool.begin()
    conn.run_sql("""INSERT INTO groups (title, description, owner, "type", startdate, enddate)
               VALUES (%s, %s, %s, %s, %s, %s);""", (name, description, owner, grouptype, startdate, enddate))
    res = conn.run_sql("SELECT currval('groups_id_seq')")
    log(INFO, "create('%s', '%s', %d, %d) Added Group" % (name, description, owner, grouptype))
    dbpool.commit(conn)
    if res:
        return int(res[0][0])
    log(INFO, "create('%s', '%s', %d, %d, %s, %s) FAILED" % (name, description, owner, grouptype, startdate, enddate))
    return None


def getUsersInGroup(group):
    """ Return a list of users in the group. """
    ret = run_sql("""SELECT userid FROM usergroups WHERE groupid=%s;""", (int(group),))
    if ret:
        users = [int(row[0]) for row in ret]
        return users
    log(INFO, "Request for users in unknown or empty group %s." % group)
    return []


def getName(group):
    """ Return the name of the group."""
    ret = run_sql("""SELECT title FROM groups WHERE "id"=%s;""", (group,))
    if ret:
        return ret[0][0]
    log(WARN, "Request for users in unknown or empty group %s." % group)
    return "UNKNOWN"


def addUserToGroup(uid, gid):
    """ Adds given user to the list of people enrolled in the given group."""
    run_sql("""INSERT INTO usergroups (userid, groupid, "type") VALUES (%s, %s, 2) """, (uid, gid))


def getInfo(group):
    """ Return a summary of the group.
        { 'id':id, 'name':name, 'title':title }
    """
    ret = run_sql("""SELECT id, title, description, startdate, enddate FROM groups WHERE id = %s;""", (group,))
    info = {}
    if ret:
        info = {
            'id': ret[0][0],
            'name': ret[0][1],
            'title': ret[0][2],
            'startdate': ret[0][3],
            'enddate': ret[0][4]
        }
        if info['enddate']:
            if info['enddate'] >= datetime.datetime.now():
                info['current'] = True
            else:
                info['current'] = False
        else:
            info['current'] = True
    return info


def flushUsersInGroup(gid):
    """ DANGEROUS:  Clears list of enrolled users in group.
        Use only just before importing new list.
    """
    run_sql("""DELETE FROM usergroups WHERE groupid = %s;""", (gid,))
