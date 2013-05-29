""" Time Periods.

    Support for semesters/terms/etc.

    Used mainly by Groups
"""

from ..lib.DB import run_sql


class Period(object):
    """ A time period is relatively simple, mainly just name and
        start and finish.
    """

    def __init__(self, name=None, title=None, start=None, finish=None, code=None):
        """ If just name or code is provided, load existing database
            record or raise KeyError.

            If rest is provided, create a new one. Raise KeyError if there's
            already an entry with the same name or code.
        """

        if not start:  # search
            if name:
                self._fetch_by_name(name)
            elif code:
                self._fetch_by_code(code)
            else:
                raise ValueError("Incorrect arguments provided.")
        else:  # create new
            self.name = name
            self.title = title
            self.start = start
            self.finish = finish
            self.code = code
            self.new = True

    def _fetch_by_name(self, name):
        """ If an existing record exists with this name, load it and
            return.
        """

        sql = """SELECT name, title, start, finish, code
                 FROM periods
                 WHERE name=%s;"""
        params = (name,)
        ret = run_sql(sql, params)
        if not ret:
            raise KeyError("Time Period with name '%s' not found" % name)

        self.name = ret[0][0]
        self.title = ret[0][1]
        self.start = ret[0][2]
        self.finish = ret[0][3]
        self.code = ret[0][4]
        self.new = False

        return

    def _fetch_by_code(self, code):
        """ If an existing record exists with this code, load it and
            return.
        """

        sql = """SELECT name, title, start, finish, code
                 FROM periods
                 WHERE code=%s;"""
        params = (code,)
        ret = run_sql(sql, params)
        if not ret:
            raise KeyError("Time Period with code '%s' not found" % code)

        self.name = ret[0][0]
        self.title = ret[0][1]
        self.start = ret[0][2]
        self.finish = ret[0][3]
        self.code = ret[0][4]
        self.new = False

        return

    def save(self):
        """ Save ourselves back to database.
        """

        if self.new:
            sql = """INSERT INTO periods ("name", "title", "start", "finish", "code")
                       VALUES (%s, %s, %s, %s,%s);"""
            params = (self.name, self.title, self.start, self.finish, self.code)
            ret = run_sql(sql, params)
            self.new = False
            return

        sql = """UPDATE periods
                 SET name=%s, title=%s, start=%s, finish=%s, code=%s
                 WHERE name=%s;"""
        params = (self.name, self.title, self.start, self.finish, self.code,
                  self.name)
        ret = run_sql(sql, params)