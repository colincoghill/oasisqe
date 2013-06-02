# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Groups.py
    Handle group related operations.
"""

import datetime
from oasis.lib.DB import run_sql, dbpool
from logging import log, WARN, INFO


def create(name, description, owner, grouptype, startdate=None, enddate=None):
    """ Add a group to the database. """
    conn = dbpool.begin()
    conn.run_sql("""INSERT INTO groups (title, description, owner, "type", startdate, enddate)
                    VALUES (%s, %s, %s, %s, %s, %s);""",
                 (name, description, owner, grouptype, startdate, enddate))
    res = conn.run_sql("SELECT currval('groups_id_seq')")
    log(INFO,
        "create('%s', '%s', %d, %d) Added Group" % (
        name, description, owner, grouptype))
    dbpool.commit(conn)
    if res:
        return int(res[0][0])
    log(INFO,
        "create('%s', '%s', %d, %d, %s, %s) FAILED" % (
        name, description, owner, grouptype, startdate, enddate))
    return None


def get_users(group_id):
    """ Return a list of users in the group. """
    ret = run_sql("""SELECT userid FROM usergroups WHERE groupid=%s;""",
                  (int(group_id),))
    if ret:
        users = [int(row[0]) for row in ret]
        return users
    log(INFO, "Request for users in unknown or empty group %s." % group_id)
    return []


def get_name(group_id):
    """ Return the name of the group."""
    ret = run_sql("""SELECT title FROM groups WHERE "id"=%s;""", (group_id,))
    if ret:
        return ret[0][0]
    log(WARN, "Request for users in unknown or empty group %s." % group_id)
    return "UNKNOWN"


def add_user(uid, group_id):
    """ Adds given user to the list of people enrolled in the given group."""
    run_sql(
        """INSERT INTO usergroups (userid, groupid, "type")
           VALUES (%s, %s, 2) """,
        (uid, group_id))


def get_dict(group_id):
    """ Return a summary of the group.
        { 'id':id, 'name':name, 'title':title }
    """
    ret = run_sql(
        """SELECT id, title, description, startdate, enddate
           FROM groups
           WHERE id = %s;""",
        (group_id,))
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


def flush_users_in_group(group_id):
    """ DANGEROUS:  Clears list of enrolled users in group.
        Use only just before importing new list.
    """
    run_sql("""DELETE FROM usergroups WHERE groupid = %s;""", (group_id,))


def get_course(group_id):
    """ Return the course_id of the course this group is associated with.
    """

    ret = run_sql("""SELECT course FROM groupcourses WHERE groupid=%s;""",
                  (group_id,))
    if ret:
        return int(ret[0][0])
    raise KeyError


def get_all_dict():
    """ Return a summary of all active groups, sorted by name
        [position] = { 'id':id, 'title':title }

    """
    ret = run_sql(
        """SELECT id, title, description, startdate, enddate, owner,
                  semester, "type", enrol_type, enrol_location
           FROM groups
           WHERE startdate>NOW()
             OR enddate>NOW()
           ORDER BY title ;""")
    info = {}
    if ret:
        count = 0
        for row in ret:
            info[count] = {
                'id': int(row[0]),
                'title': row[1],
                'description': row[2],
                'startdate': row[3],
                'enddate': row[4],
                'owner': row[5],
                'semester': row[6],
                'type': row[7],
                'enrol_type': row[8],
                'enrol_location': row[9]
            }
            count += 1
    return info


class Group(object):
    """ Look after groups of users.
    """

    def __init__(self,
                 id=None,
                 name=None,
                 title=None,
                 gtype=None,
                 active=None,
                 source=None,
                 period=None,
                 feed=None):
        """ If just id is provided, load existing database
            record or raise KeyError.

            If rest is provided, create a new one. Raise KeyError if there's
            already an entry with the same name or code.
        """

        if not name:  # search
            if id:
                self._fetch_by_id(id)
            else:
                raise ValueError("Must provide group ID or other fields")
        else:  # create new
            self.id = 0
            self.name = name
            self.title = title
            self.gtype = gtype
            self.active = active
            self.source = source
            self.period = period
            self.feed = feed

    def _fetch_by_id(self, g_id):
        """ Initialise from database, or KeyError
        """

        sql = """SELECT "name", "title", "gtype", "active",
                        "source", "period", "feed"
                 FROM "ugroups"
                 WHERE id=%s;"""
        params = (g_id,)
        ret = run_sql(sql, params)
        if not ret:
            raise KeyError("Group with id '%s' not found" % g_id)

        self.id = g_id
        self.name = ret[0][0]
        self.title = ret[0][1]
        self.gtype = ret[0][2]
        self.active = ret[0][3]
        self.source = ret[0][4]
        self.period = ret[0][5]
        self.feed = ret[0][6]

        return


def get_by_feed(feed_id):
    """ Return a summary of all active or future groups with the given feed
    """
    ret = run_sql(
        """SELECT "id"
           FROM "ugroups"
           WHERE "active" = TRUE
           AND "feed" = %s;""",
        (feed_id,))
    groups = []
    if ret:
        for row in ret:
            groups.append(Group(id=row[0]))

    return groups


def get_by_period(period_id):
    """ Return a summary of all active or future groups with the given feed
    """
    ret = run_sql(
        """SELECT "id"
           FROM "ugroups"
           WHERE "active" = TRUE
           AND "period" = %s;""",
        (period_id,))
    groups = []
    if ret:
        for row in ret:
            groups.append(Group(id=row[0]))

    return groups
