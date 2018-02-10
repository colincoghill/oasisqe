# -*- coding: utf-8 -*-

""" LTI Consumers

    Other eLearning software can use the LTI protocol to embed OASIS content.

    eg. Moodle
"""

from oasis.lib.DB import run_sql


# CREATE TABLE lti_consumers (
#    "id" SERIAL PRIMARY KEY,
#    "short_name" character varying(20) unique NOT NULL,
#    "title" character varying(250),
#    "shared_secret" character varying,
#    "consumer_key" character varying,
#    "comments" character varying,
#    "active" BOOLEAN default FALSE,
#    "lastseen" timestamp with time ZONE
# );

class LTIConsumer(object):
    """ An LTIConsumer can consume our content.
    """

    def __init__(self, ltic_id=None, short_name=None,
                 title=None, shared_secret=None, consumer_key=None,
                 comments=None, active=None):
        """ If just id is provided, load existing database
            record or raise KeyError.

            If rest is provided, create a new one. Raise KeyError if there's
            already an entry with the same name or code.
        """

        if not active:  # search
            if ltic_id:
                self._fetch_by_id(ltic_id)
            else:
                if consumer_key:
                    self._fetch_by_consumer_key(consumer_key)

        else:  # create new
            self.ltic_id = 0
            self.short_name = short_name
            self.title = title
            self.shared_secret = shared_secret
            self.consumer_key = consumer_key
            self.comments = comments
            self.lastseen = None
            self.error = ""
            self.active = active
            self.new = True

    def _fetch_by_id(self, ltic_id):
        """ If an existing record exists with this id, load it and
            return.
        """
        sql = """SELECT "id", "short_name", "title", "shared_secret", "consumer_key", "comments", "active", "lastseen"
                 FROM "lti_consumers"
                 WHERE "id"=%s;"""
        params = [ltic_id, ]
        ret = run_sql(sql, params)
        if not ret:
            raise KeyError("LTIConsumer with id '%s' not found" % ltic_id)

        self.id = ltic_id
        self.short_name = ret[0][1]
        self.title = ret[0][2]
        self.shared_secret = ret[0][3]
        self.consumer_key = ret[0][4]
        self.comments = ret[0][5]
        self.active = ret[0][6]
        self.lastseen = ret[0][7]
        self.new = False
        if not self.short_name:
            self.name = ""
        if not self.title:
            self.title = ""
        return


    def _fetch_by_consumer_key(self, consumer_key):
        """ If an existing record exists with this consumer_key, load it and
            return.
        """
        sql = """SELECT "id", "short_name", "title", "shared_secret", "consumer_key", "comments", "active", "lastseen"
                 FROM "lti_consumers"
                 WHERE "consumer_key"=%s;"""
        params = [consumer_key, ]
        ret = run_sql(sql, params)
        if not ret:
            raise KeyError("LTIConsumer with consumer_key '%s' not found" % consumer_key)

        self.id = ret[0][0]
        self.short_name = ret[0][1]
        self.title = ret[0][2]
        self.shared_secret = ret[0][3]
        self.consumer_key = ret[0][4]
        self.comments = ret[0][5]
        self.active = ret[0][6]
        self.lastseen = ret[0][7]
        self.new = False
        if not self.short_name:
            self.name = ""
        if not self.title:
            self.title = ""
        return


    def save(self):
        """ Save ourselves back to database.
        """

        if self.new:
            sql = """INSERT INTO "lti_consumers" ("short_name", "title", "shared_secret", "consumer_key", "comments", "active")
                       VALUES (%s, %s, %s, %s, %s, %s);"""
            params = [self.short_name, self.title, self.shared_secret, self.consumer_key,
                      self.comments, self.active]
            run_sql(sql, params)
            self.new = False
            return

        sql = """UPDATE "lti_consumers"
                 SET "short_name" = %s,
                     "title" = %s,
                     "shared_secret" = %s,
                     "consumer_key" = %s,
                     "comments" = %s,
                     "active" = %s
                 WHERE "id" = %s;"""
        params = [self.short_name, self.title, self.shared_secret, self.consumer_key,
                  self.comments, self.active, self.id]

        run_sql(sql, params)



def all_list():
    """
        Return a list of all LTI Consumers
    """
    sql = """SELECT "id" FROM "lti_consumers";"""
    ret = run_sql(sql)
    if not ret:
        return []

    lti_consumers = []
    for row in ret:
        ltic_id = row[0]
        lti_consumers.append(LTIConsumer(ltic_id=ltic_id))

    return lti_consumers

