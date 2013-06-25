# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Groups.py
    Handle group related operations.
"""


# Dev note:  Currently pulling these things into objects. Once most of the
# things that front the database are objects, will then investigate an ORM
# like SQL Alchemy. Too big a jump to do it all in one go.

from oasis.lib import Periods
from oasis.lib.DB import run_sql, IntegrityError
# from logging import log, WARN, INFO


class Group(object):
    """ Look after groups of users.
    """

    def __init__(self,
                 g_id=None,
                 name=None,
                 title=None,
                 gtype=None,
                 active=None,
                 source=None,
                 period=None,
                 feed=None,
                 feedargs=None):
        """ If id is provided, load existing database
            record or raise KeyError.

            If gtype is provided, create a new one and raise KeyError if there's
            already an entry with the same name or code.
        """

        if not g_id:  # new
            self.id = 0
            self.name = name
            self.title = title
            self.gtype = gtype
            self.active = active
            self.source = source
            self.period = period
            self._period_obj = None
            self.feed = feed
            self.feedargs = feedargs

        if g_id:
            self._fetch_by_id(g_id)

    def _fetch_by_id(self, g_id):
        """ Initialise from database, or KeyError
        """
        sql = """SELECT "name", "title", "gtype", "active",
                        "source", "period", "feed", "feedargs"
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
        self._period_obj = None
        self.feed = ret[0][6]
        self.feedargs = ret[0][7]

        return

    def members(self):
        """ Return a list of userids in the group. """
        ret = run_sql("""SELECT userid FROM usergroups WHERE groupid=%s;""",
                      (self.id,))
        if ret:
            users = [int(row[0]) for row in ret]
            return users
        return []

    def add_member(self, uid):
        """ Adds given user to the group."""
        run_sql(
            """INSERT INTO usergroups (userid, groupid)
               VALUES (%s, %s) """,
            (uid, self.id))

    def remove_member(self, uid):
        """ Remove given user from the group."""
        run_sql(
            """DELETE FROM usergroups
               WHERE groupid=%s AND userid=%s;""",
            (self.id, uid))

    def flush_members(self):
        """ DANGEROUS:  Clears list of enrolled users in group.
            Use only just before importing new list.
        """
        run_sql("""DELETE FROM usergroups WHERE groupid = %s;""", (self.id,))

    def save(self):
        """ Store us back to database.
        """
        if not self.id:  # it's a new one
            sql = """INSERT INTO ugroups ("name", "title", "gtype", "source",
                                        "active", "period", "feed", "feedargs")
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"""
            params = (self.name, self.title, self.gtype, self.source,
                      self.active, self.period, self.feed, self.feedargs)
            try:
                run_sql(sql, params)
            except IntegrityError:
                try:
                    exists = Group(name=self.name)
                except KeyError:
                    pass
                else:
                    if exists.id != self.id:
                        raise ValueError("Group with that name already exists")

            return

        sql = """UPDATE ugroups
                 SET name=%s, title=%s, gtype=%s, source=%s,
                     active=%s, period=%s, feed=%s, feedargs=%s
                 WHERE id=%s;"""
        params = (self.name, self.title, self.gtype, self.source,
                  self.active, self.period, self.feed, self.feedargs,
                  self.id)
        try:
            run_sql(sql, params)
        except IntegrityError:
            try:
                exists = Group(name=self.name)
            except KeyError:
                pass
            else:
                if exists.id != self.id:
                    raise ValueError("Group with that name already exists")

    def size(self):
        """ How many people are in the group?
        """

        return len(self.members())

    def period_name(self):
        """ Human name for period
        """

        sql = """SELECT name FROM periods WHERE id=%s;"""
        params = (self.period,)
        ret = run_sql(sql, params)
        if not ret:
            return 'unknown'
        return ret[0][0]

    def period_obj(self):
        """ Period object
        """
        if not self._period_obj:
            self._period_obj = Periods.Period(self.period)
        return self._period_obj


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
            groups.append(Group(g_id=row[0]))

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
            groups.append(Group(g_id=row[0]))

    return groups


def get_ids_by_name(name):
        """ Return any groups (list of ids) with the given name
        """
        sql = """SELECT "id"
                 FROM "ugroups"
                 WHERE name=%s;"""
        params = (name,)
        ret = run_sql(sql, params)
        if not ret:
            return []
        groups = []

        for row in ret:
            groups.append([int(row[0])])

        return groups


def get_by_name(name):
        """ Return (the first) group with the given name
        """
        sql = """SELECT "id"
                 FROM "ugroups"
                 WHERE name=%s;"""
        params = (name,)
        ret = run_sql(sql, params)
        if not ret:
            return 0
        return Group(g_id=int(ret[0][0]))


def active_by_course(course_id):
    """ Return a summary of all active or future groups with the given feed
    """
    ret = run_sql(
        """SELECT "ugroups"."id"
           FROM "ugroups", "groupcourses", "periods"
           WHERE "ugroups"."active" = TRUE
             AND "groupcourses"."groupid" = "ugroups"."id"
             AND "groupcourses"."course" = %s
             AND "ugroups"."period" = "periods"."id"
             AND "periods"."finish" > NOW();;""",
        (course_id,))
    groups = {}
    if ret:
        for row in ret:
            groups[row[0]] = Group(g_id=row[0])

    return groups


def all_groups():
    """ Return a summary of all groups
    """
    ret = run_sql(
        """SELECT "id"
           FROM "ugroups";""")
    groups = []
    if ret:
        for row in ret:
            groups.append(Group(g_id=row[0]))

    return groups


def enrolment_groups():
    """ Return a summary of all active enrolment groups
        Active means current or near future
    """
    ret = run_sql(
        """SELECT "ugroups"."id"
           FROM "ugroups", "periods"
           WHERE "ugroups"."gtype" = 2
             AND "ugroups"."active" = TRUE
             AND "ugroups"."period" = "periods"."id"
             AND "periods"."finish" > NOW();""")  # gtype 2 =  enrolment
    groups = {}
    if ret:
        for row in ret:
            groups[row[0]] = Group(g_id=row[0])

    return groups


def all_gtypes():
    """ Return a summary of all group types
    """

    ret = run_sql(
        """SELECT "type", "title", "description"
           FROM "grouptypes";""")
    gtypes = []
    if ret:
        for row in ret:
            gtypes.append({
                'type': int(row[0]),
                'title': row[1],
                'description': row[2]
            })

    return gtypes
