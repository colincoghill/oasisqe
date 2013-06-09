# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Groups.py
    Handle group related operations.
"""


# Dev note:  Currently pulling these things into objects. Once most of the
# things that front the database are objects, will then investigate an ORM
# like SQL Alchemy. Too big a jump to do it all in one go.


from oasis.lib.DB import run_sql
# from logging import log, WARN, INFO


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
            """INSERT INTO usergroups (userid, groupid, "type")
               VALUES (%s, %s, 2) """,
            (uid, self.id))

    def flush_members(self):
        """ DANGEROUS:  Clears list of enrolled users in group.
            Use only just before importing new list.
        """
        run_sql("""DELETE FROM usergroups WHERE groupid = %s;""", (self.id,))


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


def get_active_by_course(course_id):
    """ Return a summary of all active or future groups with the given feed
    """
    ret = run_sql(
        """SELECT "ugroups"."id"
           FROM "ugroups", "groupcourses"
           WHERE "ugroups"."active" = TRUE
           AND "groupcourses"."group" = "ugroups"."id"
           AND "groupcourses"."course" = %s;""",
        (course_id,))
    groups = []
    if ret:
        for row in ret:
            groups.append(Group(id=row[0]))

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
            groups.append(Group(id=row[0]))

    return groups

