# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Connection pooling for both memcached and for the database connection,
    since they don't appear to be very threadsafe. It also helps keep
    the number of database connections down.
"""

import Queue
import os
import OaConfig

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_SERIALIZABLE
import memcache
from logging import log, INFO, WARNING, ERROR

try:
    uniqueKey = OaConfig.uniqueKey
except AttributeError:
    uniqueKey = OaConfig.parentURL
log(INFO, "Unique key set to '%s'." % uniqueKey,)


class DbConn:
    """Manage a single database connection."""

    def __init__(self, connectstring):

        self.connectstring = connectstring
        self.conn = psycopg2.connect(connectstring)
        self.conn.set_isolation_level(ISOLATION_LEVEL_SERIALIZABLE)
        log(INFO, "DB Encoding is %s" % self.conn.encoding)
        if not self.conn:
            log(INFO, "DB relogin failed!")

    def run_sql(self, sql, params=None, quiet=False):
        """ Execute SQL commands over the connection. """
        try:
            cur = self.conn.cursor()
            if not params:
                rec = cur.execute(sql)
            else:
                rec = cur.execute(sql, params)

        except BaseException, err:
            # it's possible that database connection timed out. Try once more.
            if not quiet:
                log(ERROR, "DB Error (%s) '%s' (%s)" % (err, sql, repr(params)))
                raise
            return None

        if sql.split()[0].upper() in ("SELECT", "SHOW", "DESC", "DESCRIBE"):
            recset = cur.fetchall()
            return recset
        else:
            return rec

    def commit(self):
        """End the current transaction """
        self.conn.commit()


class DbPool:
    """ Manage a pool of DbConn.
        users should grab a database connection with begin(), run sql
        commands with run_sql() and then release it back to the pool with
        commit(). This also signifies one transaction.
        Will initialise the pool with the given number of parallel connections.

        example:

        dbpool = DbPool("dbname=oasis user=oasisuser",10)
        dbc = dbpool.begin()
        dbc.run_sql("SELECT * FROM users WHERE user=%s;", userid)
        dbpool.commit(dbc)
    """

    def __init__(self, connectstring, size):
        self.connqueue = Queue.Queue(size)
        for _ in range(0, size):
            self.connqueue.put(DbConn(connectstring))

    def begin(self):
        """Fetch a db connection from the pool (will block until one becomes
           available), and begin a transaction on it.
        """
        if self.connqueue.qsize() < 3:
            log(INFO, "DB Pool getting low! %d" % self.connqueue.qsize())
        dbc = self.connqueue.get(True)
        # psycopg2 automatically does a transaction begin for us,
        return dbc

    def commit(self, dbc):
        """Commit the transaction and put the db connection back in the pool."""
        dbc.commit()
        # TODO: Check to see if there were any errors before putting it back
        self.connqueue.put(dbc)


class fileCache:
    """Cache data in local files """

    def __init__(self, cachedir):

        if not os.access(cachedir, os.W_OK):
            try:
                os.makedirs(cachedir)
            except BaseException, err:
                log(INFO,
                    "Can't create file cache in %s (%s)" % (cachedir, err))
        self.cachedir = cachedir

    def set(self, key, value):
        """ store item."""
        if value is False:
            # We want to delete the item from the cache
            try:
                os.unlink("%s/%s/DATA" % (self.cachedir, key))
            except OSError:
                # this usually happens when the file is already gone
                pass
            return
        if not os.access("%s/%s" % (self.cachedir, key), os.W_OK):
            try:
                os.makedirs("%s/%s" % (self.cachedir, key))
            except IOError:
                log(ERROR,
                    "Can't create cache in %s/%s" % (self.cachedir, key))
        try:
            # create with temporary name to avoid concurrent access issues
            fname = os.tempnam("%s/%s" % (self.cachedir, key), "oatmp")
            fptr = open(fname, "w")
            fptr.write(value)
            fptr.close()
            os.rename(fname, "%s/%s/DATA" % (self.cachedir, key))
        except IOError, err:
            log(ERROR,
                "File Cache Error. (%s)" % err)
            return False
        return True

    def getFilename(self, key):
        """ return the full path to the on-disk file """
        try:
            fptr = open("%s/%s/DATA" % (self.cachedir, key), "r")
        except IOError:
            return False, False
        fptr.close()
        return "%s/%s/DATA" % (self.cachedir, key), True

    def get(self, key):
        """ fetch item. """
        try:
            fptr = open("%s/%s/DATA" % (self.cachedir, key), "r")
        except IOError:
            return False, False
        try:
            data = fptr.read()
            fptr.close()
            if len(data) == 0:
                log(ERROR, "file Cache EMPTY retreival. (key=%s)" % (key,))
                data = False
        except IOError, err:
            # it's possible that something went wrong
            log(ERROR, "file Cache ERROR. (key=%s, exception=%s)" % (key, err))
            return False, False
        return data, True


# noinspection PyUnusedLocal
class FakeMCConn:
    """ Dummy memcached connector for when we don't want to use memcached.
    """

    def __init__(self, connectstring):
        log(INFO, "Starting dummy memcached interface.")

    def set(self, key, value, expiry=None):
        """Pretend to store item. """
        return True

    def get(self, key):
        """Return nothing. """
        return None

    def delete(self, key):
        """Do nothing."""
        return None


class MCConn:
    """ Look after a connection to a memcached server.
        Just a simple wrapper with some logging. """

    def __init__(self, connectstring):

        self.conn = memcache.Client([connectstring], debug=0)
        if not self.conn:
            log(ERROR,
                "Memcache login failed!")

    def set(self, key, value, expiry=None):
        """ store item. """
        key = "%s-%s" % (uniqueKey, key)
        key = key.encode("utf-8")
        try:
            if expiry:
                res = self.conn.set(key, value, expiry)
            else:
                res = self.conn.set(key, value)
            log(INFO,
                "OaPool:MCConn:set(%s, %s, %s)" % (key, value, expiry))
        except BaseException, err:
            # it's possible that something went wrong
            log(ERROR, "Memcache Error. (%s)" % err)
            return False

        return res

    def get(self, key):
        """ fetch item."""
        key = "%s-%s" % (uniqueKey, key)
        key = key.encode("utf-8")
        try:
            res = self.conn.get(key)

        except BaseException, err:
            # it's possible that something went wrong
            log(ERROR,
                "Memcache Error. (%s)" % err)
            return False

        return res

    def delete(self, key):
        """ remove item."""
        key = "%s-%s" % (uniqueKey, key)
        key = key.encode("utf-8")
        try:
            res = self.conn.delete(key)

        except IOError, err:
            # it's possible that something went wrong
            log(ERROR,
                "Memcache Error. (%s)" % err)
            return False

        return res


# nowadays memcache-client comes with its own pool, but this works and I haven't
# had time to evaluate the memcache one.
class MCPool:
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
            log(WARNING,
                "Memcache Pool getting low! %d" % self.connqueue.qsize())
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




