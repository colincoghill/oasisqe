# -*- coding: utf-8 -*-

""" Test various database issues that have come up over time, make sure
    they're fixed and don't reoccur.
"""

# TODO: Get this into its own test DB!
# Currently it'll walk all over the live database.

from oasis.lib import OaConfig
from oasis.lib import Pool

dbpool = Pool.DbPool(OaConfig.oasisdbconnectstring, 5)


def test_simple_store():
    """
    Try some basic DB operations.
    """

    conn = dbpool.begin()
    conn.run_sql(
        """CREATE TABLE IF NOT EXISTS testcase_one (
             "key" INTEGER,
             "value" TEXT
           );
        """)
    conn.run_sql("""INSERT INTO testcase_one ("key", "value") VALUES (42, '12345');""")
    res = conn.run_sql("""SELECT "key", "value" FROM testcase_one WHERE "key" = 42;""")
    assert res[0][1] == "12345"
    conn.run_sql("DROP TABLE testcase_one;")
    dbpool.commit(conn)


def test_transaction_safety():
    """
    This is really hard to test, but gotta at least try something.
    """

    # Currently crashes!?
    # setup
    conn = dbpool.begin()
    conn.run_sql(
        """CREATE TABLE IF NOT EXISTS testcase_two (
             "name" VARCHAR(20),
             "value" TEXT
           );
        """)

    dbpool.commit(conn)

    # hit the same thing from two parallel transactions
    conn1 = dbpool.begin()
    conn2 = dbpool.begin()
    conn1.run_sql("""INSERT INTO testcase_two ("name", "value") VALUES ('a', '12345');""")
    conn2.run_sql("""INSERT INTO testcase_two ("name", "value") VALUES ('b', 'abcdef');""")
    dbpool.commit(conn1)
    dbpool.commit(conn2)

    # fetch the result.
    conn3 = dbpool.begin()
    res = conn3.run_sql("""SELECT "name", "value" FROM testcase_two WHERE "name" = 'a';""")
    dbpool.commit(conn3)

    # we don't actually care which one, as long as one did.
    print res[0][1]

    # clean up
    conn = dbpool.begin()
    conn.run_sql("DROP TABLE testcase_two;")
    dbpool.commit(conn)