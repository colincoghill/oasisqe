# -*- coding: utf-8 -*-

""" Enrolment Feeds

    Support for importing enrolment data from elsewhere

    Used mainly by Groups
"""

from oasis.lib.DB import run_sql


class Feed(object):
    """ A feed object tells us about the feed and where to get the scripts
        that do the main work of importing.
    """

    def __init__(self, f_id=None, name=None,
                 title=None, script=None, envvar=None,
                 comments=None, freq=None, active=None):
        """ If just id is provided, load existing database
            record or raise KeyError.

            If rest is provided, create a new one. Raise KeyError if there's
            already an entry with the same name or code.
        """

        if not active:  # search
            if f_id:
                self._fetch_by_id(f_id)

        else:  # create new
            self.id = 0
            self.name = name
            self.title = title
            self.script = script
            self.envvar = envvar
            self.comments = comments
            self.freq = freq
            self.status = "new"
            self.error = ""
            self.active = active
            self.new = True

    def _fetch_by_id(self, feed_id):
        """ If an existing record exists with this id, load it and
            return.
        """
        sql = """SELECT name, title, script, envvar, comments, freq,
                        status, error, active
                 FROM feeds
                 WHERE id=%s;"""
        params = [feed_id, ]
        ret = run_sql(sql, params)
        if not ret:
            raise KeyError("Feed with id '%s' not found" % feed_id)

        self.id = feed_id
        self.name = ret[0][0]
        self.title = ret[0][1]
        self.script = ret[0][2]
        self.envvar = ret[0][3]
        self.comments = ret[0][4]
        self.freq = ret[0][5]
        self.status = ret[0][6]
        self.error = ret[0][7]
        self.active = ret[0][8]
        self.new = False
        if not self.name:
            self.name = ""
        if not self.title:
            self.title = ""
        return

    def save(self):
        """ Save ourselves back to database.
        """

        if self.new:
            sql = """INSERT INTO feeds ("name", "title", "script", "envvar",
                                        "comments", "freq", "status", "error",
                                        "active")
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"""
            params = [self.name, self.title, self.script, self.envvar,
                      self.comments, self.freq, self.status, self.error,
                      self.active]
            run_sql(sql, params)
            self.new = False
            return

        sql = """UPDATE feeds
                 SET name = %s,
                     title = %s,
                     script = %s,
                     envvar = %s,
                     comments = %s,
                     freq = %s,
                     status = %s,
                     error = %s,
                     active = %s
                 WHERE id = %s;"""
        params = [self.name, self.title, self.script, self.envvar,
                  self.comments, self.freq, self.status, self.error,
                  self.active, self.id]

        run_sql(sql, params)

    def freq_name(self):
        """ Feed frequency as a human readable word.
        """

        if self.freq in ('1', 1):
            return "hourly"
        if self.freq in ('2', 2):
            return "daily"
        if self.freq in ('3', 3):
            return "manual"
        return "unknown"


def all_list():
    """
        Return a list of all time periods in the system.
    """
    #  Need a way to do this with one query.
    sql = """SELECT id FROM feeds;"""
    ret = run_sql(sql)
    if not ret:
        return []

    feeds = []
    for row in ret:
        feed_id = row[0]
        feeds.append(Feed(f_id=feed_id))

    return feeds


def active_hourly():
    """
        Return a list of active hourly feeds.
    """
    #  Need a way to do this with one query.
    sql = """SELECT id FROM feeds WHERE active=True AND freq='1';"""
    ret = run_sql(sql)
    if not ret:
        return []

    feeds = []
    for row in ret:
        feed_id = row[0]
        feeds.append(Feed(f_id=feed_id))

    return feeds


def active_daily():
    """
        Return a list of active daily feeds.
    """
    #  Need a way to do this with one query.
    sql = """SELECT id FROM feeds WHERE active=True AND freq='2';"""
    ret = run_sql(sql)
    if not ret:
        return []

    feeds = []
    for row in ret:
        feed_id = row[0]
        feeds.append(Feed(f_id=feed_id))

    return feeds
