# -*- coding: utf-8 -*-

""" LTI Consumers

    Other eLearning software can use the LTI protocol to embed OASIS content.

    eg. Moodle
"""

from oasis.lib.DB import run_sql

from oasis import app


# CREATE TABLE lti_consumers (
#    "id" SERIAL PRIMARY KEY,
#    "title" character varying(250),
#    "shared_secret" character varying,
#    "username_attribute" character varying,
#    "consumer_key" character varying,
#    "comments" character varying,
#    "active" BOOLEAN default FALSE,
#    "last_seen" timestamp with time ZONE
# );

class LTIConsumer(object):
    """ An LTIConsumer can consume our content.
    """

    def __init__(self, ltic_id=None, consumer_key=None,
                 title=None, shared_secret=None, username_attribute=None,
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
            if not username_attribute:
                username_attribute = "name"
            self.ltic_id = 0
            self.title = title
            self.shared_secret = shared_secret
            self.username_attribute = username_attribute
            self.consumer_key = consumer_key
            self.comments = comments
            self.last_seen = None
            self.error = ""
            self.active = active
            self.new = True

    def _fetch_by_id(self, ltic_id):
        """ If an existing record exists with this id, load it and
            return.
        """
        sql = """SELECT "id", "title", "shared_secret", "consumer_key", "comments", "active", "last_seen", "username_attribute"
                 FROM "lti_consumers"
                 WHERE "id"=%s;"""
        params = [ltic_id, ]
        ret = run_sql(sql, params)
        if not ret:
            raise KeyError("LTIConsumer with id '%s' not found" % ltic_id)

        self.id = ltic_id
        self.title = ret[0][1]
        self.shared_secret = ret[0][2]
        self.consumer_key = ret[0][3]
        self.comments = ret[0][4]
        self.active = ret[0][5]
        self.last_seen = ret[0][6]
        self.username_attribute = ret[0][7]
        self.new = False
        return


    def _fetch_by_consumer_key(self, consumer_key):
        """ If an existing record exists with this consumer_key, load it and
            return.
        """
        sql = """SELECT "id", "title", "shared_secret", "consumer_key", "comments", "active", "last_seen", "username_attribute"
                 FROM "lti_consumers"
                 WHERE "consumer_key"=%s;"""
        params = [consumer_key, ]
        ret = run_sql(sql, params)
        if not ret:
            raise KeyError("LTIConsumer with consumer_key '%s' not found" % consumer_key)

        self.id = ret[0][0]
        self.title = ret[0][1]
        self.shared_secret = ret[0][2]
        self.consumer_key = ret[0][3]
        self.comments = ret[0][4]
        self.active = ret[0][5]
        self.last_seen = ret[0][6]
        self.username_attribute = ret[0][7]
        self.new = False
        return


    def save(self):
        """ Save ourselves back to database.
        """

        if self.new:
            sql = """INSERT INTO "lti_consumers" ("title", "shared_secret", "consumer_key", "comments", "active")
                       VALUES (%s, %s, %s, %s, %s);"""
            params = [self.title, self.shared_secret, self.consumer_key,
                      self.comments, self.active]
            run_sql(sql, params)
            self.new = False
            update_lti_config()
            return

        sql = """UPDATE "lti_consumers"
                 SET "title" = %s,
                     "shared_secret" = %s,
                     "username_attribute" = %s,
                     "consumer_key" = %s,
                     "comments" = %s,
                     "active" = %s
                 WHERE "id" = %s;"""
        params = [self.title, self.shared_secret, self.username_attribute, self.consumer_key,
                  self.comments, self.active, self.id]

        run_sql(sql, params)
        update_lti_config()


def all_list(active=False):
    """
        Return a list of all LTI Consumers
    """

    if active:
        sql = """SELECT "id" FROM "lti_consumers" WHERE active=TRUE;"""
    else:
        sql = """SELECT "id" FROM "lti_consumers";"""

    ret = run_sql(sql)
    if not ret:
        return []

    lti_consumers = []
    for row in ret:
        ltic_id = row[0]
        lti_consumers.append(LTIConsumer(ltic_id=ltic_id))

    return lti_consumers


def update_lti_config():
    """ pylti library wants LTI configuration set in an app variable"""

    lti_consumers = all_list(active=True)
    consumers = dict()
    for consumer in lti_consumers:
        consumers[consumer.consumer_key] = {
            'secret': consumer.shared_secret
        }

    app.config['PYLTI_CONFIG'] = {
        'consumers': consumers,
        'roles': {
            'admin': ['Administrator', 'urn:lti:instrole:ims/lis/Administrator'],
            'student': ['Student', 'urn:lti:instrole:ims/lis/Student']
        }
    }