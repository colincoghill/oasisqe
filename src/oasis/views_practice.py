# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Views related to the practice section
"""

import os

from flask import render_template, session, request, abort
from logging import log, ERROR
from .lib import OaDB, OaPractice, Topics, OaGeneral, CourseAPI, OaSetup
MYPATH = os.path.dirname(__file__)
from .lib.OaUserDB import check_perm

from oasis import app, authenticated


@app.route("/practice/top")
@authenticated
def practice_top():
    """ Present the top level practice page - let them choose a course """
    return render_template(
        "practicetop.html",
        courses=OaSetup.get_sorted_courselist()
    )


@app.route("/practice/coursequestions/<int:course_id>")
@authenticated
def practice_choose_topic(course_id):
    """ Present a list of topics for them to choose from the given course """
    user_id = session['user_id']
    try:
        course = CourseAPI.get_course(course_id)
    except KeyError:
        course = None
        abort(404)
    try:
        topics = CourseAPI.get_topics_list(course_id)
    except KeyError:
        topics = []
        abort(404)
    return render_template(
        "practicecourse.html",
        courses=OaSetup.get_sorted_courselist(),
        canpreview=check_perm(user_id, course_id, "OASIS_PREVIEWQUESTIONS"),
        topics=topics,
        course=course
    )


@app.route("/practice/subcategory/<int:topic_id>")
@authenticated
def practice_choose_question(topic_id):
    """ Present a list of questions for them to choose from the given topic """
    user_id = session['user_id']
    try:
        course_id = Topics.get_course_id(topic_id)
    except KeyError:
        course_id = None
        abort(404)
    topics = []
    try:
        topics = CourseAPI.get_topics_list(course_id)
    except KeyError:
        abort(404)
    try:
        course = CourseAPI.get_course(course_id)
    except KeyError:
        course = None
        abort(404)
    topictitle = Topics.get_name(topic_id)
    questions = OaPractice.get_sorted_questions(course_id, topic_id, user_id)

    return render_template(
        "practicetopic.html",
        canpreview=check_perm(user_id, course_id, "OASIS_PREVIEWQUESTIONS"),
        topics=topics,
        topic_id=topic_id,
        course=course,
        topictitle=topictitle,
        questions=questions
    )


@app.route("/practice/statsfortopic/<int:topic_id>")
@authenticated
def practice_choose_question_stats(topic_id):
    """ Present a list of questions for them to choose from the given topic,
        and show some statistics on how they're doing.
    """
    user_id = session['user_id']

    course_id = Topics.get_course_id(topic_id)
    if not course_id:
        abort(404)

    topics = CourseAPI.get_topics_list(course_id)
    course = CourseAPI.get_course(course_id)
    topictitle = Topics.get_name(topic_id)
    questions = OaPractice.get_sorted_questions_wstats(course_id, topic_id, user_id)

    return render_template(
        "practicetopicstats.html",
        canpreview=check_perm(user_id, course_id, "OASIS_PREVIEWQUESTIONS"),
        topics=topics,
        topic_id=topic_id,
        course=course,
        topictitle=topictitle,
        questions=questions
    )


@app.route("/practice/question/<int:topic_id>/<int:qtemplate_id>",
           methods=['POST', 'GET'])
@authenticated
def practice_do_question(topic_id, qtemplate_id):
    """ Show them a question and allow them to fill in some answers """
    user_id = session['user_id']
    try:
        course_id = Topics.get_course_id(topic_id)
    except KeyError:
        course_id = None
        abort(404)
    try:
        course = CourseAPI.get_course(course_id)
    except KeyError:
        course = None
        abort(404)
    topictitle = "UNKNOWN"
    try:
        topictitle = Topics.get_name(topic_id)
    except KeyError:
        abort(404)
    try:
        qt = OaDB.get_qtemplate(qtemplate_id)
    except KeyError:
        qt = None
        abort(404)
    questions = OaPractice.get_sorted_questions(course_id, topic_id, user_id)
    q_title = qt['title']
    q_pos = OaDB.get_qtemplate_topic_pos(qtemplate_id, topic_id)

    blocked = OaPractice.is_q_blocked(user_id, course_id, topic_id, qtemplate_id)
    if blocked:
        return render_template(
            "practicequestionblocked.html",
            mesg=blocked,
            topictitle=topictitle,
            topic_id=topic_id,
            qt_id=qtemplate_id,
            course=course,
            q_title=q_title,
            questions=questions,
            q_pos=q_pos,
        )

    try:
        q_id = OaPractice.get_practice_q(qtemplate_id, user_id)
    except (ValueError, TypeError), err:
        log(ERROR, "OaPracticeBE:getPracticeQuestion(%s,%s) FAILED 1! %s" % (qtemplate_id, user_id, err))
        return render_template(
            "practicequestionerror.html",
            mesg="Error generating question.",
            topictitle=topictitle,
            topic_id=topic_id,
            qt_id=qtemplate_id,
            course=course,
            q_title=q_title,
            questions=questions,
            q_pos="?",
        )

    if not q_id > 0:
        return render_template(
            "practicequestionerror.html",
            mesg="Error generating question.",
            topictitle=topictitle,
            topic_id=topic_id,
            qt_id=qtemplate_id,
            course=course,
            q_title=q_title,
            questions=questions,
            q_pos="?",
        )

    q_body = OaGeneral.render_q_html(q_id)
    q_body = q_body.replace(r"\240", u" ")  # TODO: why is this here?

    return render_template(
        "practicedoquestion.html",
        q_body=q_body,
        topictitle=topictitle,
        topic_id=topic_id,
        qt_id=qtemplate_id,
        course=course,
        q_title=q_title,
        questions=questions,
        q_pos=q_pos,
        q_id=q_id,
    )


@app.route("/practice/markquestion/<int:topic_id>/<int:question_id>",
           methods=['POST', ])
@authenticated
def practice_mark_question(topic_id, question_id):
    """ Mark the submitted question answersjust wa """
    user_id = session['user_id']

    course_id = Topics.get_course_id(topic_id)
    if not course_id:
        abort(404)

    course = CourseAPI.get_course(course_id)
    if not course:
        abort(404)

    topictitle = "UNKNOWN"
    try:
        topictitle = Topics.get_name(topic_id)
    except KeyError:
        abort(404)

    qt_id = OaDB.get_q_parent(question_id)

    q_title = OaDB.get_qt_name(qt_id)
    questions = OaPractice.get_sorted_questions(course_id, topic_id, user_id)
    q_pos = OaDB.get_qtemplate_topic_pos(qt_id, topic_id)

    blocked = OaPractice.is_q_blocked(user_id, course_id, topic_id, qt_id)
    if blocked:
        return render_template(
            "practicequestionblocked.html",
            mesg=blocked,
            topictitle=topictitle,
            topic_id=topic_id,
            qt_id=qt_id,
            course=course,
            q_title=q_title,
            questions=questions,
            q_pos=q_pos,
        )

    marking = OaPractice.mark_q(user_id, topic_id, question_id, request)
    prev_id, next_id = OaPractice.get_next_prev(qt_id, topic_id)

    return render_template(
        "practicemarkquestion.html",
        topictitle=topictitle,
        topic_id=topic_id,
        qt_id=qt_id,
        course=course,
        q_title=q_title,
        questions=questions,
        q_pos=q_pos,
        q_id=question_id,
        marking=marking,
        next_id=next_id,
        prev_id=prev_id
    )

