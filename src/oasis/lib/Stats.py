# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" OaStats.py
    This provides a collection of methods for generating statistics from
    the database. Most results will be placed back into the database for
    other components to use.
"""

from datetime import datetime, timedelta
import DB


def prac_q_count(year, month, day, hour, qtemplate):
    """ Fetch the practice count for the given time/qtemplate or return
        False if not found. Can be used when deciding if to INSERT or UPDATE.
        Note: may return 0 if count is zero, is not same as not exist (False)
    """
    sql = """SELECT "qtemplate", "hour", "day", "month", "year", "number", "when"
                FROM stats_prac_q_course
                 WHERE hour=%s
                 AND month=%s
                 AND day=%s
                 AND year=%s
                 AND qtemplate=%s;"""
    params = (hour, month, day, year, qtemplate)
    res = DB.run_sql(sql, params)
    if not res or len(res) == 0:
        return False
    return int(res[0][0])


def add_prac_q_count(year, month, day, hour, qtemplate, count, avgscore):
    """ Insert a practice count for the given time/qtemplate """
    sql = """INSERT INTO stats_prac_q_course ("qtemplate", "hour", "day",
                                              "month", "year", "number",
                                              "when", "avgscore")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"""
    params = (qtemplate,  hour, day,
              month, year, count,
              datetime(year=year, hour=hour, day=day, month=month), avgscore)
    DB.run_sql(sql, params)


def update_prac_q_count(year, month, day, hour, qtemplate, count, avgscore):
    """ Insert a practice count for the given time/qtemplate """
    sql = """UPDATE stats_prac_q_course SET "number"=%s, "avgscore"=%s
                 WHERE hour=%s
                 AND month=%s
                 AND day=%s
                 AND year=%s
                 AND qtemplate=%s;"""
    params = (count, avgscore, hour, month, day, year, qtemplate)
    DB.run_sql(sql, params)


def populate_prac_q_count(start=None, end=None):
    """  Go through the questions from start to end date and count the number of
         questions practiced. Store the results in stats_prac_q_course
         If start not given, go back to the start of the database. If end not
         given go until now.
    """
    if not end:
        end = datetime.now()
    if not start:
        start = datetime(2000, 1, 1)

    sql = """ SELECT COUNT(question) AS practices,
                EXTRACT (YEAR FROM marktime) as year,
                     EXTRACT (MONTH FROM marktime) as month,
                     EXTRACT (DAY FROM marktime) as day,
                     EXTRACT (HOUR FROM marktime) as hour,
                     qtemplate AS qtemplate,
                     AVG(score) AS avgscore
              FROM questions
              WHERE (exam = '0' or exam is null)
              AND marktime >= %s
              AND marktime <= %s
              GROUP BY
                     EXTRACT (YEAR FROM marktime),
                     EXTRACT (MONTH FROM marktime),
                     EXTRACT (DAY FROM marktime),
                     EXTRACT (HOUR FROM marktime),
                     qtemplate;
                     """
    params = (start, end)
    res = DB.run_sql(sql, params)
    if not res:
        return False
    for row in res:
        data = {
            'count': int(row[0]),
            'year': int(row[1]),
            'month': int(row[2]),
            'day': int(row[3]),
            'hour': int(row[4]),
            'qtemplate': int(row[5]),
            'avgscore': float(row[6])
        }
        exist_count = prac_q_count(data['year'],
                                   data['month'],
                                   data['day'],
                                   data['hour'],
                                   data['qtemplate'])
        if exist_count is False:  # could be 0
            add_prac_q_count(data['year'],
                             data['month'],
                             data['day'],
                             data['hour'],
                             data['qtemplate'],
                             data['count'],
                             data['avgscore'])
        else:
            update_prac_q_count(data['year'],
                                data['month'],
                                data['day'],
                                data['hour'],
                                data['qtemplate'],
                                data['count'],
                                data['avgscore'])


def daily_prac_q_count(start_time, end_time, qt_id):
    """ Return a list of daily count of practices for the given qtemplate
        over the time period
    """
    sql = """SELECT "year", "month", "day", sum("number")
             FROM "stats_prac_q_course"
             WHERE "qtemplate"=%s
               AND "when" >= %s
               AND "when" <= %s
             GROUP BY "year","month","day"
             ORDER BY "year","month","day" ASC;"""
    params = (qt_id, start_time, end_time)
    res = DB.run_sql(sql, params)
    if not res:
        res = []
    data = []
    first = True
    for row in res:
        if first:  # if the data doesn't start with a value,
                   # set a 0 entry so graphs scale correctly
            if not (int(row[1]) == start_time.month
                    and int(row[2]) == start_time.day
                    and int(row[0] == start_time.year)):
                data.append(("%04d-%02d-%02d" % (start_time.year, start_time.month, start_time.day), 0))
            first = False

        dt = datetime.strptime("%04d-%02d-%02d" % (int(row[0]), int(row[1]), int(row[2])), "%Y-%m-%d")
        data.append((dt.strftime("%Y-%m-%d"), int(row[3])))

    if len(res) >= 1 and not data[-1][0] == "%04d-%02d-%02d" % (end_time.year, end_time.month, end_time.day):
        data.append(("%04d-%02d-%02d" % (end_time.year, end_time.month, end_time.day), 0))
    return data
#
#
# def daily_prac_q_scores(start_time, end_time, qt_id):
#     """ Return a list of daily count of practices for the given qtemplate over
#        the time period
#     """
#     sql = """SELECT "year", "month", "day", sum("number"), sum("avgscore")
#              FROM "stats_prac_q_course"
#              WHERE "qtemplate"=%s
#                AND "when" >= %s
#                AND "when" <= %s
#              GROUP BY "year","month","day"
#              ORDER BY "year","month","day" ASC;"""
#     params = (qt_id, start_time, end_time)
#     res = DB.run_sql(sql, params)
#     if not res:
#         res = []
#     data = []
#     first = True
#     for row in res:
#         if first: # if the data doesn't start with any values, set a 0 entry,
#                   #  so graphs scale correctly
#             if not (int(row[1]) == start_time.month
#                     and int(row[2]) == start_time.day
#                     and int(row[0] == start_time.year)):
#
#                 data.append(("%04d-%02d-%02d" % (start_time.year, start_time.month, start_time.day), 0))
#             first = False
#         dt = datetime.strptime("%04d-%02d-%02d" %(int(row[0]), int(row[1]), int(row[2])), "%Y-%m-%d")
#         data.append((dt.strftime("%Y-%m-%d"), row[4] / row[3]))
#     if len(res) >= 1 \
#         and not data[-1][0] == "%04d-%02d-%02d" % (end_time.year, end_time.month, end_time.day):
#
#         data.append(("%04d-%02d-%02d" % (end_time.year, end_time.month, end_time.day), 0))
#     return data


def daily_prac_load(start_time, end_time):
    """ Return a list of daily counts of practices for the whole system """
    sql = """SELECT "year", "month", "day", sum("number") from "stats_prac_q_course"
             WHERE "when" >= %s
               AND "when" <= %s
             GROUP BY "year","month","day"
             ORDER BY "year","month","day" ASC;"""
    params = (start_time, end_time)
    res = DB.run_sql(sql, params)
    if not res:
        res = []
    data = []
    first = True
    for row in res:
        if first:  # if the data doesn't start with any values, set a 0 entry,
                   # so graphs scale correctly
            if not (int(row[1]) == start_time.month
                    and int(row[2]) == start_time.day
                    and int(row[0] == start_time.year)):
                data.append(("%04d-%02d-%02d" % (start_time.year, start_time.month, start_time.day), 0))
            first = False
        dt = datetime.strptime("%04d-%02d-%02d" % (int(row[0]), int(row[1]), int(row[2])), "%Y-%m-%d")
        data.append((dt.strftime("%Y-%m-%d"), row[3]))
    if len(res) >= 1 and not data[-1][0] == "%04d-%02d-%02d" % (end_time.year, end_time.month, end_time.day):

        data.append(("%04d-%02d-%02d" % (end_time.year, end_time.month, end_time.day), 0))
    return data


def do_daily_stats_update():
    """ To be run daily. Will update stats for the last few days to now.
        Do the last two weeks, should cover most temporary outages
    """

    now = datetime.now()
    twoweek = timedelta(days=14)
    st = now-twoweek
    populate_prac_q_count(start=st)


def do_initial_stats_update():
    """ To be run once, on upgrade from a system that didn't do this.
        Will update stats from the beginning of the database, to now.
        May take a while.
    """

    now = datetime.now()
    st = datetime(1990, 1, 1)
    populate_prac_q_count(start=st, end=now)



