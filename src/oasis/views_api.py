# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" URLs designed to be called by other code - generally to return
    JSON for AJAX calls from the web interface
"""

import os
import datetime


from flask import session, abort, jsonify, request
# from logging import log, ERROR, INFO
from oasis.lib import Exams, API, Stats

MYPATH = os.path.dirname(__file__)

from oasis.lib.Permissions import satisfy_perms
from oasis.lib import Users

from oasis import app, authenticated, require_perm


@app.route("/api/exam/<int:course_id>/<int:exam_id>/qtemplates")
@authenticated
def api_exam_qtemplates(course_id, exam_id):
    """ Return a JSON list of all the qtemplates used for the given exam.
    """
    user_id = session['user_id']
    if not satisfy_perms(user_id, course_id, ("examcreate",)):
        abort(401)

    if exam_id == 0:   # New assessment may be being created
        return jsonify(result=[[{'qtid': 0}, ], ])

    exam = Exams.get_exam_struct(exam_id)
    ecid = exam['cid']
    if not ecid == course_id:   # They may be trying to bypass permission check
        abort(401)

    qtemplates = []
    try:
        qtemplates = Exams.get_qts_list(exam_id)
    except KeyError:
        abort(401)

    return jsonify(result=qtemplates)


@app.route("/api/stats/practice/qtemplate/<int:qt_id>/<int:year>")
@authenticated
def api_stats_qtemplates_year(qt_id, year):
    """ Return the number of times the qtemplate was practiced in
        the given year, broken down by day
    """
    start_time = datetime.datetime(year=year, month=1, day=1, hour=0)
    end_time = datetime.datetime(year=year, month=12, day=31, hour=23)

    counts = Stats.daily_prac_q_count(start_time, end_time, qt_id)
    return jsonify(result=counts)

#
# @app.route("/api/stats/practice/qtemplate/<int:qt_id>/<int:year>/scores")
# @authenticated
# def api_stats_qt_year_scores(qt_id, year):
#     """ Return the number of times the qtemplate was practiced in the given
#         year, broken down by day
#     """
#     start_time = datetime.datetime(year=year, month=1, day=1, hour=0)
#     end_time = datetime.datetime(year=year, month=12, day=31, hour=23)
#
#     scores = Stats.daily_prac_q_scores(start_time, end_time, qt_id)
#     return jsonify(result=scores)
#
#
# @app.route("/api/stats/practice/qtemplate/<int:qt_id>/3months/scores")
# @authenticated
# def api_stats_qtemplates_3month_scores(qt_id):
#     """ Return the number of times the qtemplate was practiced in approx
#         the last three months
#     """
#     month3 = datetime.timedelta(weeks=12)
#     days3 = datetime.timedelta(days=3)
#
#     now = datetime.datetime.now()
#     end_time = now+days3
#     start_time = now-month3
#
#     scores = Stats.daily_prac_q_scores(start_time, end_time, qt_id)
#     return jsonify(result=scores)


@app.route("/api/stats/practice/qtemplate/<int:qt_id>/3months")
@authenticated
def api_stats_qtemplates_3month(qt_id):
    """ Return the number of times the qtemplate was practiced in approx
        the last three months
    """
    month3 = datetime.timedelta(weeks=12)
    days3 = datetime.timedelta(days=3)

    now = datetime.datetime.now()
    end_time = now+days3
    start_time = now-month3

    counts = Stats.daily_prac_q_count(start_time, end_time, qt_id)
    return jsonify(result=counts)


@app.route("/api/stats/practice/3months")
@authenticated
def api_stats_practice_load():
    """ Return the number of times any qtemplate was practiced in
        approx the last three months
    """
    month3 = datetime.timedelta(weeks=12)
    days3 = datetime.timedelta(days=3)

    now = datetime.datetime.now()
    end_time = now+days3
    start_time = now-month3

    counts = Stats.daily_prac_load(start_time, end_time)
    return jsonify(result=counts)


@app.route("/api/stats/practice/<int:year>")
@authenticated
def api_stats_practice_load_year(year):
    """ Return the number of times any qtemplate was practiced in the
        given year, broken down by day
    """
    start_time = datetime.datetime(year=year, month=1, day=1, hour=0)
    end_time = datetime.datetime(year=year, month=12, day=31, hour=23)

    counts = Stats.daily_prac_load(start_time, end_time)
    return jsonify(result=counts)


# noinspection PyUnusedLocal
@app.route("/api/exam/<int:course_id>/<int:exam_id>/available_qtemplates")
@authenticated
def api_exam_available_qtemplates(course_id, exam_id):
    """ Present a list of qtemplates that are available for use in the exam."""
    if 'user_id' not in session:
        abort(401)
    user_id = session['user_id']
    if not satisfy_perms(user_id, course_id, ("examcreate",)):
        abort(401)

    return jsonify(result=API.exam_available_q_list(course_id))


@app.route("/api/users/typeahead")
@require_perm('useradmin')
def api_users_typeahead():
    """ Take a partially typed user name and return records that match it.
    """
    # TODO: This doesn't work!?
    needle = request.form["term"]
    if not needle:
        matches = ['eric', 'ernie', 'columbia']
    else:
        matches = Users.typeahead(needle)
    return jsonify(result=matches)
