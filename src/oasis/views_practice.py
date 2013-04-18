# -*- coding: utf-8 -*-

""" Views related to the practice section
"""

import os

from flask import render_template, session, request, abort
from logging import log, ERROR
from .lib import OaDB, OaPractice, Topics, OaGeneral, CourseAPI, OaSetup
MYPATH = os.path.dirname(__file__)
from .lib.OaUserDB import checkPermission

from oasis import app, authenticated


@app.route("/practice/top")
@authenticated
def practice_top():
    """ Present the top level practice page - let them choose a course """
    return render_template(
        "practicetop.html",
        courses=OaSetup.getSortedCourseList()
    )


@app.route("/practice/coursequestions/<int:course_id>")
@authenticated
def practice_choose_topic(course_id):
    """ Present a list of topics for them to choose from the given course """
    user_id = session['user_id']
    try:
        course = CourseAPI.getCourse(course_id)
    except KeyError:
        course = None
        abort(404)
    try:
        topics = CourseAPI.getTopicsListInCourse(course_id)
    except KeyError:
        topics = []
        abort(404)
    return render_template(
        "practicecourse.html",
        courses=OaSetup.getSortedCourseList(),
        canpreview=checkPermission(user_id, course_id, "OASIS_PREVIEWQUESTIONS"),
        topics=topics,
        course=course
    )


@app.route("/practice/subcategory/<int:topic_id>")
@authenticated
def practice_choose_question(topic_id):
    """ Present a list of questions for them to choose from the given topic """
    user_id = session['user_id']
    try:
        course_id = Topics.getCourse(topic_id)
    except KeyError:
        course_id = None
        abort(404)
    topics = []
    try:
        topics = CourseAPI.getTopicsListInCourse(course_id)
    except KeyError:
        abort(404)
    try:
        course = CourseAPI.getCourse(course_id)
    except KeyError:
        course = None
        abort(404)
    topictitle = Topics.getName(topic_id)
    questions = OaPractice.getSortedQuestionList(course_id, topic_id, user_id)

    return render_template(
        "practicetopic.html",
        canpreview=checkPermission(user_id, course_id, "OASIS_PREVIEWQUESTIONS"),
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

    course_id = Topics.getCourse(topic_id)
    if not course_id:
        abort(404)

    topics = CourseAPI.getTopicsListInCourse(course_id)
    course = CourseAPI.getCourse(course_id)
    topictitle = Topics.getName(topic_id)
    questions = OaPractice.getSortedQuestionListWithStats(course_id, topic_id, user_id)

    return render_template(
        "practicetopicstats.html",
        canpreview=checkPermission(user_id, course_id, "OASIS_PREVIEWQUESTIONS"),
        topics=topics,
        topic_id=topic_id,
        course=course,
        topictitle=topictitle,
        questions=questions
    )


@app.route("/practice/question/<int:topic_id>/<int:qtemplate_id>", methods=['POST', 'GET'])
@authenticated
def practice_do_question(topic_id, qtemplate_id):
    """ Show them a question and allow them to fill in some answers """
    user_id = session['user_id']
    try:
        course_id = Topics.getCourse(topic_id)
    except KeyError:
        course_id = None
        abort(404)
    try:
        course = CourseAPI.getCourse(course_id)
    except KeyError:
        course = None
        abort(404)
    topictitle = "UNKNOWN"
    try:
        topictitle = Topics.getName(topic_id)
    except KeyError:
        abort(404)
    try:
        qt = OaDB.getQTemplate(qtemplate_id)
    except KeyError:
        qt = None
        abort(404)
    questions = OaPractice.getSortedQuestionList(course_id, topic_id, user_id)
    q_title = qt['title']
    q_pos = OaDB.getQTemplatePositionInTopic(qtemplate_id, topic_id)

    blocked = OaPractice.isQuestionBlockedToUser(user_id, course_id, topic_id, qtemplate_id)
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
        q_id = int(OaPractice.getPracticeQuestion(qtemplate_id, user_id))
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

    try:
        q_body = OaGeneral.renderQuestionHTML(q_id)
        q_body = q_body.replace(u"\240", u" ")
    except (ValueError, TypeError, KeyError), err:
        log(ERROR, "OaPracticeBE:getPracticeQuestion(%s,%s) FAILED 2! %s" % (qtemplate_id, user_id, err))
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


@app.route("/practice/markquestion/<int:topic_id>/<int:question_id>", methods=['POST'])
@authenticated
def practice_mark_question(topic_id, question_id):
    """ Mark the submitted question answersjust wa """
    user_id = session['user_id']

    course_id = Topics.getCourse(topic_id)
    if not course_id:
        abort(404)

    course = CourseAPI.getCourse(course_id)
    if not course:
        abort(404)

    topictitle = "UNKNOWN"
    try:
        topictitle = Topics.getName(topic_id)
    except KeyError:
        abort(404)

    qt_id = OaDB.getQuestionParent(question_id)

    q_title = OaDB.getQTemplateName(qt_id)
    questions = OaPractice.getSortedQuestionList(course_id, topic_id, user_id)
    q_pos = OaDB.getQTemplatePositionInTopic(qt_id, topic_id)

    blocked = OaPractice.isQuestionBlockedToUser(user_id, course_id, topic_id, qt_id)
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

    marking = OaPractice.markQuestion(user_id, topic_id, question_id, request)
    prev_id, next_id = OaPractice.getNextPrev(qt_id, topic_id)

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

