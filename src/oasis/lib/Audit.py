# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Audit.py
    Handle storing and searching audit messages
"""

from oasis.lib.DB import run_sql


def audit(aclass, instigator, obj, module, message):
    """Record the message in the audit system."""
    sql = """INSERT INTO audit ("time", "class", "instigator",
                                "object", "module", "longmesg")
            VALUES (NOW(), %s, %s, %s, %s, %s);"""
    params = (aclass, instigator, obj, module, message)
    run_sql(sql, params)


def get_records_by_user(uid, start=None, end=None, limit=100, offset=0):
    """ Return audit records created by (or on behalf of) the user.
        If start is provided, only searches for records after start.
        If end is also provided, only searches between start and end.
        start and end should be datetime or None
        uid should be a user ID integer.
        limit is the maximum number of rows returned, offset is starting
        from result n
    """
    uid = int(uid)
    if end:
        sql = """SELECT "id", "instigator", "module", "longmesg",
                        "time", "object", "message"
                FROM audit
                WHERE ("object" = %s or "instigator" = %s)
                  AND "time" > %s
                  AND "time" < %s
                ORDER BY "time" DESC
                LIMIT %s OFFSET %s;"""
        params = (uid, uid, start, end, limit, offset)
    elif start:
        sql = """SELECT "id", "instigator", "module", "longmesg",
                        "time", "object", "message"
                FROM audit
                WHERE ("object" = %s or "instigator" = %s)
                  AND "time" > %s
                ORDER BY "time" DESC
                LIMIT %s OFFSET %s;"""
        params = (uid, uid, start, limit, offset)
    else:
        sql = """SELECT "id", "instigator", "module", "longmesg",
                        "time", "object", "message"
                FROM audit
                WHERE ("object" = %s OR "instigator" = %s)
                ORDER BY "time" DESC
                LIMIT %s OFFSET %s;"""
        params = (uid, uid, limit, offset)

    ret = run_sql(sql, params)
    results = []
    if ret:
        for row in ret:
            entry = {'id': row[0],
                     'instigator': row[1],
                     'module': row[2],
                     'message': row[3],
                     'time': row[4],
                     'object': row[5]}
            if not row[3]:
                entry['message'] = row[6]
            results.append(entry)
    return results
