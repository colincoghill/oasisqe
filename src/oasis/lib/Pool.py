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


import Queue
import os
import OaConfig
from logging import getLogger
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import memcache

try:
    uniqueKey = OaConfig.uniqueKey
except AttributeError:
    uniqueKey = OaConfig.parentURL

L = getLogger("oasisqe")

class DbConn(object):
    """Manage a single database connection."""

    def __init__(self, connectstring):

        self.connectstring = connectstring
        self.conn = psycopg2.connect(connectstring)
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        L.info("DB Encoding is %s" % self.conn.encoding)
        if not self.conn:
            L.warn("DB relogin failed!")

    def run_sql(self, sql, params=None, quiet=False):
        """ Execute SQL commands over the connection. """
#        log(ERROR, "DB SQL '%s' (%s)" % (sql, repr(params)))
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
        self.connqueue = Queue.Queue(size)
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


class FileCache(object):
    """Cache data in local files """

    def __init__(self, cachedir):

        if not os.access(cachedir, os.W_OK):
            try:
                os.makedirs(cachedir)
            except BaseException as err:
                L.warn("Can't create file cache in %s (%s)" % (cachedir, err))
        self.cachedir = cachedir

    def set(self, key, value):
        """ store item."""
        if value is False:
            # We want to delete the item from the cache
            try:
                os.unlink(os.path.join(self.cachedir, key, "DATA"))
            except OSError:
                # this usually happens when the file is already gone
                pass
            return
        if not os.access(os.path.join(self.cachedir, key), os.W_OK):
            try:
                os.makedirs(os.path.join(self.cachedir, key))
            except IOError:
                L.error("Can't create cache in %s/%s" % (self.cachedir, key))
        try:
            fptr = open(os.path.join(self.cachedir, key, "DATA"), "wb")
            fptr.write(value)
            fptr.close()
        except IOError as err:
            L.error("File Cache Error. (%s)" % err)
            return False
        return True

    def get_filename(self, key):
        """ return the full path to the on-disk file """
        try:
            fptr = open(os.path.join(self.cachedir, key, "DATA"), "r")
        except IOError:
            return False, False
        fptr.close()
        return os.path.join(self.cachedir, key, "DATA"), True

    def get(self, key):
        """ fetch item. """
        try:
            fptr = open(os.path.join(self.cachedir, key, "DATA"), "r")
        except IOError:
            return False, False
        try:
            data = fptr.read()
            fptr.close()
            if len(data) == 0:
                L.error("file Cache EMPTY retreival. (key=%s)" % (key,))
                data = False
        except IOError as err:
            # it's possible that something went wrong
            L.error("file Cache ERROR. (key=%s, exception=%s)" % (key, err))
            return False, False
        return data, True


# noinspection PyUnusedLocal
class FakeMCConn(object):
    """ Dummy memcached connector for when we don't want to use memcached.
    """

    def __init__(self, connectstring):
        L.info("Starting dummy memcached interface.")

    def set(self, key, value, expiry=None):
        """Pretend to store item. """
        return True

    def get(self, key):
        """Return nothing. """
        return None

    def delete(self, key):
        """Do nothing."""
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
        key = "%s-%s" % (uniqueKey, key)
        key = key.encode("utf-8")
        try:
            res = self.conn.delete(key)

        except IOError as err:
            # it's possible that something went wrong
            self.L.error("Memcache Error. (%s)" % err)
            return False

        return res


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

        self.connqueue = Queue.Queue(size)
        for _ in range(0, size):
            try:
                if not OaConfig.enableMemcache:
                    mc = FakeMCConn
                else:
                    mc = MCConn
            except AttributeError:
                mc = MCConn
            self.connqueue.put(mc(connectstring))

    def get(self, key):
        """Get an item from the cache. """
        if self.connqueue.qsize() < 3:
            L.warn("Memcache Pool getting low! %d" % self.connqueue.qsize())
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
