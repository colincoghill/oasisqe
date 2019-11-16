# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Connection pooling for both memcached and for the database connection,
    since they don't appear to be very threadsafe. It also helps keep
    the number of database connections down.
"""

# There are better ways to do this now, but this code is complex and
# has been running for literally a decade so it'll be a bit of work
# to make sure a replacement works as well.


import queue
from . import OaConfig
from logging import getLogger
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import memcache

try:
    uniqueKey = OaConfig.uniqueKey
except AttributeError:
    uniqueKey = OaConfig.parentURL

L = getLogger("oasisqe")

disable_mc_cache = False


class DbConn(object):
    """Manage a single database connection."""

    def __init__(self, connectstring):

        self.connectstring = connectstring
        self.conn = psycopg2.connect(connectstring)
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        L.info("DB Encoding is %s" % self.conn.encoding)
        if not self.conn:
            L.warning("DB relogin failed!")

    def run_sql(self, sql, params=None, quiet=False):
        """ Execute SQL commands over the connection. """
#        L.error("DB SQL '%s' (%s) quiet=%s" % (sql, repr(params), quiet))
        try:
            cur = self.conn.cursor()
            if not params:
                rec = cur.execute(sql)
            else:
                rec = cur.execute(sql, params)

        except BaseException as err:
            if not quiet:
                L.error("DB Error (%s) '%s' (%s)" % (err, sql, repr(params)))
                raise
            return None

        if (sql.split()[0].upper() in ("SELECT", "SHOW", "DESC", "DESCRIBE")
                or "RETURNING" in sql.upper()):
            recset = cur.fetchall()
            cur.close()
            return recset
        else:
            cur.close()
            return rec


class DbPool(object):
    """ Manage a pool of DbConn.
        users should grab a database connection with start(), run sql
        commands with run_sql() and then release it back to the pool with
        finish(). 
        Will initialise the pool with the given number of parallel connections.

        example:

        dbpool = DbPool("dbname=oasis user=oasisuser",10)
        dbc = dbpool.start()
        dbc.run_sql("SELECT * FROM users WHERE user=%s;", userid)
        dbpool.finish(dbc)
    """

    def __init__(self, connectstring, size):
        self.size = size
        self.connqueue = queue.Queue(size)
        for _ in range(0, size):
            self.connqueue.put(DbConn(connectstring))

    def start(self):
        """Fetch a db connection from the pool (will block until one becomes
           available), and begin a transaction on it.
        """
        if self.connqueue.qsize() < 3:
            L.info("DB Pool getting low! %d" % self.connqueue.qsize())
        dbc = self.connqueue.get(True)
        return dbc

    def finish(self, dbc):
        """Put the db connection back in the pool."""
        # TODO: check for errors and reset connection if any
        self.connqueue.put(dbc)

    def __len__(self):
        """
        :return: integer : the number of free entries in the pool.
        """
        return self.connqueue.qsize()

    def total(self):
        """
        :return: integer : the number of db connections.
        """
        return self.size


# noinspection PyUnusedLocal
class FakeMCConn(object):
    """ Dummy memcached connector for when we don't want to use memcached.
    """

    def __init__(self, connectstring):
        L.info("Starting dummy memcached interface.")

    # noinspection PyMethodMayBeStatic
    def set(self, key, value, expiry=None):
        """Pretend to store item. """
        return True

    # noinspection PyMethodMayBeStatic
    def get(self, key):
        """Return nothing. """
        return None

    # noinspection PyMethodMayBeStatic
    def delete(self, key):
        """Do nothing."""
        return None

    # noinspection PyMethodMayBeStatic
    def flush(self):
        """ Do nothing
        """
        return None


class MCConn(object):
    """ Look after a connection to a memcached server.
        Just a simple wrapper with some logging. """

    def __init__(self, connectstring):

        self.conn = memcache.Client([connectstring], debug=0)
        if not self.conn:
            L.error("Memcache login failed!")

    def set(self, key, value, expiry=None):
        """ store item. """
        if disable_mc_cache:
            return True
        key = "%s-%s" % (uniqueKey, key)
        key = key.encode("utf-8")
        try:
            if expiry:
                res = self.conn.set(key, value, expiry)
            else:
                res = self.conn.set(key, value)
            L.info("OaPool:MCConn:set(%s, %s, %s)" % (key, value, expiry))
        except BaseException as err:
            # it's possible that something went wrong
            L.error("Memcache Error. (%s)" % err)
            return False

        return res

    def get(self, key):
        """ fetch item."""
        if disable_mc_cache:
            return None
        key = "%s-%s" % (uniqueKey, key)
        key = key.encode("utf-8")
        try:
            res = self.conn.get(key)

        except BaseException as err:
            # it's possible that something went wrong
            L.error("Memcache Error. (%s)" % err)
            return False

        return res

    def delete(self, key):
        """ remove item."""
        if disable_mc_cache:
            return None
        key = "%s-%s" % (uniqueKey, key)
        key = key.encode("utf-8")
        try:
            res = self.conn.delete(key)

        except IOError as err:
            # it's possible that something went wrong
            L.error("Memcache Error. (%s)" % err)
            return False

        return res

    def flush_all(self):
        """ Clear the cache
        """
        if disable_mc_cache:
            return None
        return self.conn.flush_all()


# nowadays memcache-client comes with its own pool, but this works and I haven't
# had time to evaluate the memcache one.
class MCPool(object):
    """ Look after a pool of connections to the memcached. As well as reducing
        total number of connections used, libmemcache also doesn't appear to be
        threadsafe, so this gives us some protection.
    """

    def __init__(self, connectstring, size):
        """Call with the connection string and a number of
           connections to put in the pool.
        """

        self.connqueue = queue.Queue(size)
        self.size = size
        for _ in range(0, size):
            try:
                if not OaConfig.memcache_enable:
                    mc = FakeMCConn
                else:
                    mc = MCConn
            except AttributeError:
                mc = MCConn
            self.connqueue.put(mc(connectstring))

    def get(self, key):
        """Get an item from the cache. """
        if self.connqueue.qsize() < 3:
            L.warning("Memcache Pool getting low! %d" % self.connqueue.qsize())
        dbc = self.connqueue.get(True)
        res = dbc.get(key)
        self.connqueue.put(dbc)
        return res

    def set(self, key, value, expiry=None):
        """Put an item into the cache. """
        dbc = self.connqueue.get(True)
        res = dbc.set(key, value, expiry)
        self.connqueue.put(dbc)
        return res

    def delete(self, key):
        """Remove an item from the cache. """
        dbc = self.connqueue.get(True)
        res = dbc.delete(key)
        self.connqueue.put(dbc)
        return res

    def flush_all(self):
        """ Clear the cache
        """

        dbc = self.connqueue.get(True)
        res = dbc.flush_all()
        self.connqueue.put(dbc)
        return res

    def __len__(self):
        """
        :return: integer : the number of free entries in the pool.
        """
        return self.connqueue.qsize()

    def total(self):
        """
        :return: integer : the number of db connections.
        """
        return self.size
