# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Views related to the practice section
"""

import os

from flask import render_template, session, request, abort

from oasis.lib import DB, Practice, Topics, General, Courses2, Setup, Courses
MYPATH = os.path.dirname(__file__)
from oasis.lib.Permissions import check_perm
from logging import getLogger
import random
from oasis import app, authenticated

L = getLogger("oasisqe")

@app.route("/practice/top")
@authenticated
def practice_top():
    """ Present the top level practice page - let them choose a course """
    return render_template(
        "practicetop.html",
        courses=Setup.get_sorted_courselist()
    )


@app.route("/practice/coursequestions/<int:course_id>")
@authenticated
def practice_choose_topic(course_id):
    """ Present a list of topics for them to choose from the given course """
    user_id = session['user_id']
    try:
        course = Courses2.get_course(course_id)
    except KeyError:
        course = None
        abort(404)
    try:
        topics = Courses2.get_topics_list(course_id)
    except KeyError:
        topics = []
        abort(404)

    members = None
    for topic in topics:
        if topic['visibility'] == 2:  # course only
            if not members:
                members = Courses.get_users(course_id)
            if user_id not in members:
                topics.remove(topic)
    return render_template(
        "practicecourse.html",
        courses=Setup.get_sorted_courselist(),
        canpreview=check_perm(user_id, course_id, "questionpreview"),
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
        topics = Courses2.get_topics_list(course_id)
    except KeyError:
        abort(404)
    try:
        course = Courses2.get_course(course_id)
    except KeyError:
        course = None
        abort(404)
    topictitle = Topics.get_name(topic_id)
    questions = Practice.get_sorted_questions(course_id, topic_id, user_id)

    thistopic = Topics.get_topic(topic_id)
    members = []
    if thistopic['visibility'] == 2:  # course only
        if not members:
            members = Courses.get_users(course_id)
            if user_id not in members:
                abort(404)

    for topic in topics:
        if topic['visibility'] == 2:  # course only
            if not members:
                members = Courses.get_users(course_id)
            if user_id not in members:
                topics.remove(topic)

    return render_template(
        "practicetopic.html",
        canpreview=check_perm(user_id, course_id, "questionpreview"),
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

    topics = Courses2.get_topics_list(course_id)
    course = Courses2.get_course(course_id)
    topictitle = Topics.get_name(topic_id)
    questions = Practice.get_sorted_qlist_wstats(course_id, topic_id, user_id)

    return render_template(
        "practicetopicstats.html",
        canpreview=check_perm(user_id, course_id, "questionpreview"),
        topics=topics,
        topic_id=topic_id,
        course=course,
        topictitle=topictitle,
        questions=questions
    )


@app.route("/practice/question/<int:topic_id>/<int:position>",
           methods=['POST', 'GET'])
@authenticated
def practice_do_question(topic_id, position):
    """ Show them a question and allow them to fill in some answers """
    user_id = session['user_id']
    try:
        course_id = Topics.get_course_id(topic_id)
    except KeyError:
        course_id = None
        abort(404)
    try:
        course = Courses2.get_course(course_id)
    except KeyError:
        course = None
        abort(404)
    topictitle = "UNKNOWN"
    try:
        topictitle = Topics.get_name(topic_id)
    except KeyError:
        abort(404)
    try:
        choices = DB.get_qtemplates_in_topic_position(topic_id, position)
    except KeyError:
        choices = None
        abort(404)

    if len(choices) == 1:
        qt_id = choices[0]
    elif len(choices) > 1:
        L.debug("Practice choosing random from: %s" % repr(choices))
        qt_id = random.choice(choices)
    else:
        L.warn("Access to non existent practice topic %s question %s" % (topic_id, position))
        return render_template(
            "practicequestionerror.html",
            mesg="Error accessing question.",
            topic_id=topic_id,
            course=course,
            q_pos=position
        )

    qtemplate = DB.get_qtemplate(qt_id)

    questions = Practice.get_sorted_questions(course_id, topic_id, user_id)
    q_title = qtemplate['title']
    q_pos = DB.get_qtemplate_topic_pos(qt_id, topic_id)

    blocked = Practice.is_q_blocked(user_id, course_id, topic_id, qt_id)
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

    try:
        q_id = Practice.get_practice_q(qt_id, user_id)
    except (ValueError, TypeError) as err:
        L.error("ERROR 1001  (%s,%s) %s" % (qt_id, user_id, err))
        return render_template(
            "practicequestionerror.html",
            mesg="Error generating question.",
            topictitle=topictitle,
            topic_id=topic_id,
            qt_id=qt_id,
            course=course,
            q_title=q_title,
            questions=questions,
            q_pos=q_pos,
        )

    if not q_id > 0:
        L.error("ERROR 1002  (%s,%s) Question not generated" % (qt_id, user_id))
        return render_template(
            "practicequestionerror.html",
            mesg="Error generating question.",
            topictitle=topictitle,
            topic_id=topic_id,
            qt_id=qt_id,
            course=course,
            q_title=q_title,
            questions=questions,
            q_pos=q_pos,
        )

    q_body = General.render_q_html(q_id)
    q_body = q_body.replace(r"\240", u" ")  # TODO: why is this here?

    return render_template(
        "practicedoquestion.html",
        q_body=q_body,
        topictitle=topictitle,
        topic_id=topic_id,
        qt_id=qt_id,
        course=course,
        q_title=q_title,
        questions=questions,
        q_pos=q_pos,
        q_id=q_id,
    )


# TODO: refactor - with above method
@app.route("/practice/questionid/<int:topic_id>/<int:qt_id>",
           methods=['POST', 'GET'])
@authenticated
def practice_do_question_id(topic_id, qt_id):
    """ Show them a question and allow them to fill in some answers """
    user_id = session['user_id']
    try:
        course_id = Topics.get_course_id(topic_id)
    except KeyError:
        course_id = None
        abort(404)
    try:
        course = Courses2.get_course(course_id)
    except KeyError:
        course = None
        abort(404)
    topictitle = "UNKNOWN"
    try:
        topictitle = Topics.get_name(topic_id)
    except KeyError:
        abort(404)

    qtemplate = DB.get_qtemplate(qt_id)

    questions = Practice.get_sorted_questions(course_id, topic_id, user_id)
    q_title = qtemplate['title']
    q_pos = DB.get_qtemplate_topic_pos(qt_id, topic_id)

    blocked = Practice.is_q_blocked(user_id, course_id, topic_id, qt_id)
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

    try:
        q_id = Practice.get_practice_q(qt_id, user_id)
    except (ValueError, TypeError) as err:
        L.error("ERROR 1001  (%s,%s) %s" % (qt_id, user_id, err))
        return render_template(
            "practicequestionerror.html",
            mesg="Error generating question.",
            topictitle=topictitle,
            topic_id=topic_id,
            qt_id=qt_id,
            course=course,
            q_title=q_title,
            questions=questions,
            q_pos=q_pos,
        )

    if not q_id > 0:
        L.error("ERROR 1002  (%s,%s) Question not generated" % (qt_id, user_id))
        return render_template(
            "practicequestionerror.html",
            mesg="Error generating question.",
            topictitle=topictitle,
            topic_id=topic_id,
            qt_id=qt_id,
            course=course,
            q_title=q_title,
            questions=questions,
            q_pos=q_pos,
        )

    q_body = General.render_q_html(q_id)
    q_body = q_body.replace(r"\240", u" ")  # TODO: why is this here?

    return render_template(
        "practicedoquestion.html",
        q_body=q_body,
        topictitle=topictitle,
        topic_id=topic_id,
        qt_id=qt_id,
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

    course = Courses2.get_course(course_id)
    if not course:
        abort(404)

    topictitle = "UNKNOWN"
    try:
        topictitle = Topics.get_name(topic_id)
    except KeyError:
        abort(404)

    qt_id = DB.get_q_parent(question_id)

    q_title = DB.get_qt_name(qt_id)
    questions = Practice.get_sorted_questions(course_id, topic_id, user_id)
    q_pos = DB.get_qtemplate_topic_pos(qt_id, topic_id)

    blocked = Practice.is_q_blocked(user_id, course_id, topic_id, qt_id)
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

    marking = Practice.mark_q(user_id, topic_id, question_id, request)
    prev_id, next_id = Practice.get_next_prev(qt_id, topic_id)  # TODO: need next_pos and prev_pos

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
