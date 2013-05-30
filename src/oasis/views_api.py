# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" URLs designed to be called by other code - generally to return
    JSON for AJAX calls from the web interface
"""

import os
import datetime


from flask import session, abort, jsonify

from .lib import Exams, API, Stats

MYPATH = os.path.dirname(__file__)

from .lib.UserDB import satisfyPerms

from oasis import app, authenticated


@app.route("/api/exam/<int:course_id>/<int:exam_id>/qtemplates")
@authenticated
def api_exam_qtemplates(course_id, exam_id):
    """ Return a JSON list of all the qtemplates used for the given exam.
    """
    user_id = session['user_id']
    if not satisfyPerms(user_id, course_id, ("OASIS_CREATEASSESSMENT",)):
        abort(401)

    if exam_id == 0:   # New assessment may be being created
        return jsonify(result=[[{'qtid': 0}, ], ])

    exam = Exams.getExamStruct(exam_id)
    ecid = exam['cid']
    if not ecid == course_id:   # They may be trying to bypass permission check
        abort(401)

    qtemplates = []
    try:
        qtemplates = Exams.getQTemplatesList(exam_id)
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

    counts = Stats.getQDailyPracticeCount(start_time, end_time, qt_id)
    return jsonify(result=counts)


@app.route("/api/stats/practice/qtemplate/<int:qt_id>/<int:year>/scores")
@authenticated
def api_stats_qt_year_scores(qt_id, year):
    """ Return the number of times the qtemplate was practiced in the given
        year, broken down by day
    """
    start_time = datetime.datetime(year=year, month=1, day=1, hour=0)
    end_time = datetime.datetime(year=year, month=12, day=31, hour=23)

    scores = Stats.getQDailyPracticeScores(start_time, end_time, qt_id)
    return jsonify(result=scores)


@app.route("/api/stats/practice/qtemplate/<int:qt_id>/3months/scores")
@authenticated
def api_stats_qtemplates_3month_scores(qt_id):
    """ Return the number of times the qtemplate was practiced in approx
        the last three months
    """
    month3 = datetime.timedelta(weeks=12)
    days3 = datetime.timedelta(days=3)

    now = datetime.datetime.now()
    end_time = now+days3
    start_time = now-month3

    scores = Stats.getQDailyPracticeScores(start_time, end_time, qt_id)
    return jsonify(result=scores)


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

    counts = Stats.getQDailyPracticeCount(start_time, end_time, qt_id)
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

    counts = Stats.get_daily_practice_load(start_time, end_time)
    return jsonify(result=counts)


@app.route("/api/stats/practice/<int:year>")
@authenticated
def api_stats_practice_load_year(year):
    """ Return the number of times any qtemplate was practiced in the
        given year, broken down by day
    """
    start_time = datetime.datetime(year=year, month=1, day=1, hour=0)
    end_time = datetime.datetime(year=year, month=12, day=31, hour=23)

    counts = Stats.get_daily_practice_load(start_time, end_time)
    return jsonify(result=counts)


# noinspection PyUnusedLocal
@app.route("/api/exam/<int:course_id>/<int:exam_id>/available_qtemplates")
@authenticated
def api_exam_available_qtemplates(course_id, exam_id):
    """ Present a list of qtemplates that are available for use in the exam."""
    if 'user_id' not in session:
        abort(401)
    user_id = session['user_id']
    if not satisfyPerms(user_id, course_id, ("OASIS_CREATEASSESSMENT",)):
        abort(401)

    return jsonify(result=API.getCreateExamQuestionList(course_id))
