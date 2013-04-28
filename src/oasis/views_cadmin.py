# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Course admin related pages
"""

import os
import datetime
from logging import log, ERROR
from flask import render_template, session, request, redirect, abort, url_for, flash

from .lib import OaConfig, UserAPI, OaDB, Topics, OaUserDB, OaGeneral, Exams, Courses, \
    CourseAPI, OaSetup, CourseAdmin

MYPATH = os.path.dirname(__file__)

from .lib.OaUserDB import checkPermission, satisfyPerms

from oasis import app, authenticated


@app.route("/courseadmin/top/<int:course_id>")
@authenticated
def cadmin_top(course_id):
    """ Present top level course admin page """
    user_id = session['user_id']

    course = CourseAPI.getCourse(course_id)
    if not course:
        abort(404)

    topics = CourseAPI.getTopicsListInCourse(course_id)
    exams = [Exams.getExamStruct(e, course_id) for e in Courses.getExams(course_id, previous_years=False)]

    if not satisfyPerms(user_id, course_id,
                        ("OASIS_QUESTIONEDITOR", "OASIS_VIEWMARKS", "OASIS_ALTERMARKS", "OASIS_CREATEASSESSMENT")):
        flash("You do not have admin permission on course %s" % course['name'])
        return redirect(url_for('setup_courses'))

    exams.sort(key=lambda y: y['start_epoch'], reverse=True)

    return render_template(
        "courseadmin_top.html",
        course=course,
        topics=topics,
        exams=exams
    )


@app.route("/courseadmin/config/<int:course_id>")
@authenticated
def cadmin_config(course_id):
    """ Allow some course configuration """
    user_id = session['user_id']

    course = CourseAPI.getCourse(course_id)
    if not course:
        abort(404)

    if not satisfyPerms(user_id, course_id,
                        ("OASIS_QUESTIONEDITOR", "OASIS_VIEWMARKS", "OASIS_ALTERMARKS", "OASIS_CREATEASSESSMENT")):
        flash("You do not have admin permission on course %s" % course['name'])
        return redirect(url_for('setup_courses'))

    return render_template(
        "courseadmin_config.html",
        course=course,

    )


@app.route("/courseadmin/previousassessments/<int:course_id>")
@authenticated
def cadmin_prev_assessments(course_id):
    """ Show a list of older assessments."""
    user_id = session['user_id']

    course = CourseAPI.getCourse(course_id)
    if not course:
        abort(404)

    exams = [Exams.getExamStruct(e, course_id) for e in OaDB.getCourseExamInfoAll(course_id, previous_years=True)]

    if not satisfyPerms(user_id, course_id,
                        ("OASIS_QUESTIONEDITOR", "OASIS_VIEWMARKS", "OASIS_ALTERMARKS", "OASIS_CREATEASSESSMENT")):
        flash("You do not have admin permission on course %s" % course['name'])
        return redirect(url_for('setup_courses'))

    years = [e['start'].year for e in exams]
    years = list(set(years))
    years.sort(reverse=True)
    exams.sort(key=lambda y: y['start_epoch'])
    return render_template(
        "courseadmin_previousassessments.html",
        course=course,
        exams=exams,
        years=years
    )


@app.route("/courseadmin/createexam/<int:course_id>")
@authenticated
def cadmin_create_exam(course_id):
    """ Provide a form to create/edit a new assessment """
    user_id = session['user_id']

    course = CourseAPI.getCourse(course_id)
    if not course:
        abort(404)

    topics = CourseAdmin.getCreateExamQuestionList(course_id)

    if not satisfyPerms(user_id, course_id, ("OASIS_CREATEASSESSMENT",)):
        flash("You do not have 'Create Assessment' permission on this course.")
        return redirect(url_for('cadmin_top', course_id=course_id))

    today = datetime.date.today()
    return render_template(
        "exam_edit.html",
        course=course,
        topics=topics,
        #  defaults
        exam={
            'id': 0,
            'start_date': (today + datetime.timedelta(days=1)).strftime("%a %d %b %Y"),
            'end_date': (today + datetime.timedelta(days=1)).strftime("%a %d %b %Y"),
            'start_year': today.year,
            'start_month': today.month,
            'start_day': today.day,
            'start_hour': '10',
            'start_minute': '30',
            'end_hour': '10',
            'end_minute': '30',
            'end_year': today.year,
            'end_month': today.month,
            'end_day': today.day,
            'duration': 60,
            'title': "Assessment",
            'archived': 1,
        }
    )


@app.route("/courseadmin/editexam/<int:course_id>/<int:exam_id>")
@authenticated
def cadmin_edit_exam(course_id, exam_id):
    """ Provide a form to edit an assessment """
    user_id = session['user_id']

    course = CourseAPI.getCourse(course_id)
    if not course:
        abort(404)

    exam = Exams.getExamStruct(exam_id, course_id)
    if not exam:
        abort(404)

    if not satisfyPerms(user_id, course_id, ("OASIS_CREATEASSESSMENT",)):
        flash("You do not have 'Create Assessment' permission on this course.")
        return redirect(url_for('cadmin_top', course_id=course_id))

    if not int(exam['cid']) == int(course_id):
        flash("Assessment %s does not belong to this course." % int(exam_id))
        return redirect(url_for('cadmin_top', course_id=course_id))

    return render_template(
        "exam_edit.html",
        course=course,
        exam=exam,
        test=repr(exam)
    )


@app.route("/courseadmin/exam_edit_submit/<int:course_id>/<int:exam_id>", methods=["POST", ])
@authenticated
def cadmin_edit_exam_submit(course_id, exam_id):
    """ Provide a form to edit an assessment """
    user_id = session['user_id']

    course = CourseAPI.getCourse(course_id)
    if not course:
        abort(404)

    if not satisfyPerms(user_id, course_id, ("OASIS_CREATEASSESSMENT",)):
        flash("You do not have 'Create Assessment' permission on this course.")
        return redirect(url_for('cadmin_top', course_id=course_id))

    if "exam_cancel" in request.form:
        flash("Assessment editing cancelled.")
        return redirect(url_for('cadmin_top', course_id=course_id))

    exam_id = CourseAdmin.ExamEditSubmit(request, user_id, course_id, exam_id)
    exam = Exams.getExamStruct(exam_id, course_id)
    flash("Assessment saved.")
    return render_template(
        "exam_edit_submit.html",
        course=course,
        exam=exam
    )


@app.route("/courseadmin/topics/<int:course_id>", methods=['GET', 'POST'])
@authenticated
def cadmin_edittopics(course_id):
    """ Present a page to view and edit all topics, including hidden. """
    user_id = session['user_id']

    course = None
    try:
        course = CourseAPI.getCourse(course_id)
    except KeyError:
        abort(404)

    if not course:
        abort(404)

    if not satisfyPerms(user_id, course_id, ("OASIS_QUESTIONEDITOR",)):
        flash("You do not have 'Question Editor' permission on this course.")
        return redirect(url_for('cadmin_top', course_id=course_id))

    topics = CourseAPI.getTopicsListInCourse(course_id)
    return render_template("courseadmin_edittopics.html", course=course, topics=topics)


@app.route("/courseadmin/topics_save/<int:course_id>", methods=['POST'])
@authenticated
def cadmin_edittopics_save(course_id):
    """ Accept a submitted topics page and save it."""
    user_id = session['user_id']

    course = None
    try:
        course = CourseAPI.getCourse(course_id)
    except KeyError:
        abort(404)

    if not course:
        abort(404)

    if not satisfyPerms(user_id, course_id, ("OASIS_QUESTIONEDITOR",)):
        flash("You do not have 'Question Editor' permission on this course.")
        return redirect(url_for('cadmin_top', course_id=course_id))

    if "cancel" in request.form:
        flash("Changes Cancelled!")
        return redirect(url_for('cadmin_top', course_id=course_id))

    if CourseAdmin.doCourseTopicUpdate(course, request):
        flash("Changes Saved!")
    else:
        flash("Error Saving!")
    return redirect(url_for('cadmin_edittopics', course_id=course_id))


@app.route("/courseadmin/edittopic/<int:topic_id>")
@authenticated
def cadmin_edit_topic(topic_id):
    """ Present a page to view and edit a topic, including adding/editing questions and setting some parameters."""
    user_id = session['user_id']
    course_id = None
    try:
        course_id = Topics.getCourse(topic_id)
    except KeyError:
        abort(404)

    if not course_id:
        abort(404)

    if not satisfyPerms(user_id, course_id, ("OASIS_QUESTIONEDITOR",)):
        flash("You do not have 'Question Editor' permission on this course.")
        return redirect(url_for('cadmin_top', course_id=course_id))

    course = CourseAPI.getCourse(course_id)
    topic = {
        'id': topic_id,
        'position': Topics.getPosition(topic_id),
        'name': Topics.getName(topic_id)
    }
    questions = [q for q in Topics.getQTemplates(topic_id).values()]
    for q in questions:
        q['embed_id'] = OaDB.getQTemplateEmbedID(q['id'])
        if q['embed_id']:
            q['embed_url'] = "%s/embed/question/%s/question.html" % (OaConfig.parentURL, q['embed_id'])
        else:
            q['embed_url'] = None
        q['editor'] = OaDB.getQTemplateEditor(q['id'])

    all_courses = OaGeneral.getCourseListing()
    all_courses = [c for c in all_courses if satisfyPerms(user_id, int(c['id']), (
        "OASIS_QUESTIONEDITOR", "OASIS_COURSEADMIN", "OASIS_SUPERUSER"))]
    all_courses.sort(lambda f, s: cmp(f['name'], s['name']))

    all_course_topics = []
    for c in all_courses:
        topics = Courses.getTopicsInfoAll(c['id'], numq=False)
        if topics:
            all_course_topics.append({'course': c['name'], 'topics': topics})

    questions.sort(key=lambda k: k['position'])
    return render_template(
        "courseadmin_edittopic.html",
        course=course,
        topic=topic,
        questions=questions,
        all_course_topics=all_course_topics
    )


@app.route("/courseadmin/topic/<int:topic_id>/<int:qt_id>/history")
@authenticated
def cadmin_view_qtemplate_history(topic_id, qt_id):
    """ Show the practice history of the question template. """
    user_id = session['user_id']
    course_id = None
    try:
        course_id = Topics.getCourse(topic_id)
    except KeyError:
        abort(404)

    if not course_id:
        abort(404)

    if not satisfyPerms(user_id, course_id, ("OASIS_COURSEADMIN",)):
        flash("You do not have 'Course Admin' permission on this course.")
        return redirect(url_for('cadmin_top', course_id=course_id))

    course = CourseAPI.getCourse(course_id)
    topic = {
        'id': topic_id,
        'position': Topics.getPosition(topic_id),
        'name': Topics.getName(topic_id)
    }
    qtemplate = OaDB.getQTemplate(qt_id)
    year = datetime.datetime.now().year
    years = range(year, year-6, -1)

    return render_template(
        "courseadmin_viewqtemplate.html",
        course=course,
        topic=topic,
        qtemplate=qtemplate,
        years=years
    )



@app.route("/courseadmin/topic/<int:topic_id>")
@authenticated
def cadmin_view_topic(topic_id):
    """ Present a page to view a topic, including basic stats """
    user_id = session['user_id']
    course_id = None
    try:
        course_id = Topics.getCourse(topic_id)
    except KeyError:
        abort(404)

    if not course_id:
        abort(404)

    if not satisfyPerms(user_id, course_id, ("OASIS_COURSEADMIN",)):
        flash("You do not have 'Course Admin' permission on this course.")
        return redirect(url_for('cadmin_top', course_id=course_id))

    course = CourseAPI.getCourse(course_id)
    topic = {
        'id': topic_id,
        'position': Topics.getPosition(topic_id),
        'name': Topics.getName(topic_id)
    }
    questions = [q for q in Topics.getQTemplates(topic_id).values()]
    for q in questions:
        q['embed_id'] = OaDB.getQTemplateEmbedID(q['id'])
        if q['embed_id']:
            q['embed_url'] = "%s/embed/question/%s/question.html" % (OaConfig.parentURL, q['embed_id'])
        else:
            q['embed_url'] = None
        q['editor'] = OaDB.getQTemplateEditor(q['id'])

    all_courses = OaGeneral.getCourseListing()
    all_courses = [c for c in all_courses if satisfyPerms(user_id, int(c['id']), (
        "OASIS_QUESTIONEDITOR", "OASIS_COURSEADMIN", "OASIS_SUPERUSER"))]
    all_courses.sort(lambda f, s: cmp(f['name'], s['name']))

    all_course_topics = []
    for c in all_courses:
        topics = Courses.getTopicsInfoAll(c['id'], numq=False)
        if topics:
            all_course_topics.append({'course': c['name'], 'topics': topics})

    questions.sort(key=lambda k: k['position'])
    return render_template(
        "courseadmin_viewtopic.html",
        course=course,
        topic=topic,
        questions=questions,
        all_course_topics=all_course_topics,
    )


@app.route("/courseadmin/topic_save/<int:topic_id>", methods=['POST'])
@authenticated
def cadmin_topic_save(topic_id):
    """ Receive the page from cadmin_edit_topic and process any changes. """
    user_id = session['user_id']
    course_id = None
    try:
        course_id = Topics.getCourse(topic_id)
    except KeyError:
        abort(404)

    if not course_id:
        abort(404)

    if not satisfyPerms(user_id, course_id, ("OASIS_QUESTIONEDITOR",)):
        flash("You do not have 'Question Editor' permission on this course.")
        return redirect(url_for('cadmin_top', course_id=course_id))

    if "cancel_edit" in request.form:
        flash("Topic Changes Cancelled!")
        return redirect(url_for('cadmin_top', course_id=course_id))

    if "save_changes" in request.form:
        result = OaSetup.doTopicPageCommands(request, topic_id, user_id)
        if result:
            # flash(result['mesg'])
            return redirect(url_for('cadmin_edit_topic', topic_id=topic_id))

    flash("Error saving Topic Information!")
    log(ERROR, "Error saving Topic Information " % repr(request.form))
    return redirect(url_for('cadmin_edit_topic', topic_id=topic_id))


@app.route("/courseadmin/perms/<int:course_id>")
@authenticated
def cadmin_permissions(course_id):
    """ Present a page for them to assign permissions to the course"""
    user_id = session['user_id']
    if not checkPermission(user_id, course_id, "OASIS_USERADMIN"):
        flash("You do not have user admin permissions on this course")
        return redirect(url_for('cadmin_top', course_id=course_id))
    course = CourseAPI.getCourse(course_id)

    permlist = OaUserDB.getCoursePermissions(course_id)
    perms = {}
    for uid, pid in permlist:  # (uid, permission)
        if not uid in perms:
            u = UserAPI.getUser(uid)
            perms[uid] = {
                'uname': u['uname'],
                'fullname': u['fullname'],
                'pids': []
            }
        perms[uid]['pids'].append(pid)

    return render_template(
        "courseadmin_permissions.html",
        perms=perms,
        course=course,
        pids=[5, 10, 14, 11, 8, 9, 15, 2]
    )


@app.route("/courseadmin/perms_save/<int:course_id>", methods=["POST", ])
@authenticated
def cadmin_permissions_save(course_id):
    """ Present a page for them to save new permissions to the course """
    user_id = session['user_id']
    if not checkPermission(user_id, course_id, "OASIS_USERADMIN"):
        flash("You do not have user admin permissions on this course")
        return redirect(url_for('cadmin_top', course_id=course_id))
    CourseAdmin.savePermissions(request, course_id, user_id)
    return redirect(url_for("cadmin_permissions", course_id=course_id))

