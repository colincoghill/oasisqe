# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Course admin related pages
"""

import os
from datetime import timedelta, date, datetime
from logging import log, ERROR
from flask import render_template, session, request, redirect, \
    abort, url_for, flash

from .lib import OaConfig, Users2, DB, Topics, UserDB, \
    Exams, Courses, Courses2, Setup, CourseAdmin, Groups

MYPATH = os.path.dirname(__file__)

from .lib.UserDB import satisfyPerms

from oasis import app, require_course_perm


@app.route("/cadmin/<int:course_id>/top")
@require_course_perm(("questionedit", "viewmarks",
                      "altermarks", "examcreate"),
                     redir="setup_top")
def cadmin_top(course_id):
    """ Present top level course admin page """
    course = Courses2.get_course(course_id)
    if not course:
        abort(404)

    topics = Courses2.get_topics_list(course_id)
    exams = [Exams.get_exam_struct(exam_id, course_id)
             for exam_id in Courses.get_exams(course_id, previous_years=False)]

    exams.sort(key=lambda y: y['start_epoch'], reverse=True)

    return render_template(
        "courseadmin_top.html",
        course=course,
        topics=topics,
        exams=exams
    )


@app.route("/cadmin/<int:course_id>/config")
@require_course_perm("COURSE_ADMIN")
def cadmin_config(course_id):
    """ Allow some course configuration """
    course = Courses2.get_course(course_id)
    if not course:
        abort(404)

    return render_template(
        "courseadmin_config.html",
        course=course,

    )


@app.route("/cadmin/<int:course_id>/config_submit", methods=["POST", ])
@require_course_perm("COURSE_ADMIN")
def cadmin_config_submit(course_id):
    """ Allow some course configuration """
    course = Courses2.get_course(course_id)
    if not course:
        abort(404)

    form = request.form

    if "cancel" in form:
        flash("Cancelled edit")
        return redirect(url_for("cadmin_top", course_id=course_id))

    saved = False

    new_name = form.get('name', course['name'])

    if not new_name == course['name']:
        if not (3 <= len(new_name) <= 20):
            flash("Course Name must be between 3 and 20 characters.")
        else:
            Courses.set_name(course['id'], new_name)
            saved = True

    new_title = form.get('title', course['title'])
    if not new_title == course['title']:
        if not (3 <= len(new_title) <= 100):
            flash("Course Title must be between 3 and 100 characters.")
        else:
            Courses.set_title(course['id'], new_title)
            saved = True

    registration = form.get('registration', course['registration'])
    if registration != course['registration']:
        saved = True
        Courses.set_registration(course_id, registration)

    practice_visibility = form.get('practice_visibility',
                                   course['practice_visibility'])
    if not (practice_visibility == course['practice_visibility']):
        saved = True
        Courses.set_practice_visibility(course_id, practice_visibility)

    if saved:
        flash("Changes Saved")
    else:
        flash("No changes made.")
    return redirect(url_for("cadmin_top", course_id=course_id))


@app.route("/cadmin/<int:course_id>/previousassessments")
@require_course_perm(("questionedit", "viewmarks",
                      "altermarks", "examcreate"))
def cadmin_prev_assessments(course_id):
    """ Show a list of older assessments."""
    course = Courses2.get_course(course_id)
    if not course:
        abort(404)

    exams = [Exams.get_exam_struct(exam_id, course_id)
             for exam_id in DB.get_course_exam_all(course_id, prev_years=True)]

    years = [exam['start'].year for exam in exams]
    years = list(set(years))
    years.sort(reverse=True)
    exams.sort(key=lambda y: y['start_epoch'])
    return render_template(
        "courseadmin_previousassessments.html",
        course=course,
        exams=exams,
        years=years
    )


@app.route("/cadmin/<int:course_id>/createexam")
@require_course_perm("examcreate")
def cadmin_create_exam(course_id):
    """ Provide a form to create/edit a new assessment """
    course = Courses2.get_course(course_id)
    if not course:
        abort(404)

    topics = CourseAdmin.get_create_exam_q_list(course_id)

    today = date.today()
    return render_template(
        "exam_edit.html",
        course=course,
        topics=topics,
        #  defaults
        exam={
            'id': 0,
            'start_date': (today + timedelta(days=1)).strftime("%a %d %b %Y"),
            'end_date': (today + timedelta(days=1)).strftime("%a %d %b %Y"),
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


@app.route("/cadmin/<int:course_id>/editexam/<int:exam_id>")
@require_course_perm("examcreate")
def cadmin_edit_exam(course_id, exam_id):
    """ Provide a form to edit an assessment """
    course = Courses2.get_course(course_id)
    if not course:
        abort(404)

    exam = Exams.get_exam_struct(exam_id, course_id)
    if not exam:
        abort(404)

    if not int(exam['cid']) == int(course_id):
        flash("Assessment %s does not belong to this course." % int(exam_id))
        return redirect(url_for('cadmin_top', course_id=course_id))

    return render_template(
        "exam_edit.html",
        course=course,
        exam=exam,
        test=repr(exam)
    )


@app.route("/cadmin/<int:course_id>/exam_edit_submit/<int:exam_id>",
           methods=["POST", ])
@require_course_perm("examcreate")
def cadmin_edit_exam_submit(course_id, exam_id):
    """ Provide a form to edit an assessment """
    user_id = session['user_id']

    course = Courses2.get_course(course_id)
    if not course:
        abort(404)

    if "exam_cancel" in request.form:
        flash("Assessment editing cancelled.")
        return redirect(url_for('cadmin_top', course_id=course_id))

    exam_id = CourseAdmin.exam_edit_submit(request, user_id, course_id, exam_id)
    exam = Exams.get_exam_struct(exam_id, course_id)
    flash("Assessment saved.")
    return render_template(
        "exam_edit_submit.html",
        course=course,
        exam=exam
    )


@app.route("/cadmin/<int:course_id>/enrolment")
@require_course_perm("useradmin")
def cadmin_enrolments(course_id):
    """ Present a page to view and edit all topics, including hidden. """
    user_id = session['user_id']

    course = None
    try:
        course = Courses2.get_course(course_id)
    except KeyError:
        abort(404)

    if not course:
        abort(404)

    groups = [Groups.getInfo(group_id)
              for group_id in Courses.get_groups(course_id)]

    # it's possible one was never created, legacy database, etc.
    if not len(groups):
        now = datetime.now()
        forever = datetime(year=9999, month=12, day=31)
        group_id = Groups.create(u"Staff",
                                 "Current Staff",
                                 user_id,
                                 2,
                                 startdate=now,
                                 enddate=forever)
        Courses.add_group(group_id, course_id)
        groups = [Groups.getInfo(group_id)
                  for group_id in Courses.get_groups(course_id)]
        assert len(groups)

    for group in groups:
        if not group['enddate']:
            group['enddate'] = "-"
        elif group['enddate'] > datetime(year=9990, month=1, day=1):
            group['enddate'] = "-"

        if group['startdate']:
            group['startdate'] = group['startdate'].strftime("%d %b %Y")
        else:
            group['startdate'] = "-"
        group['nummembers'] = len(Groups.get_users(group['id']))

    return render_template("courseadmin_enrolment.html",
                           course=course,
                           groups=groups)


@app.route("/cadmin/<int:course_id>/editgroup/<int:group_id>")
@require_course_perm("useradmin")
def cadmin_editgroup(course_id, group_id):
    """ Present a page for editing a group, membership, etc.
    """
    group = None
    try:
        group = Groups.getInfo(group_id)
    except KeyError:
        abort(404)

    if not group:
        abort(404)

    course = Courses2.get_course(course_id)
    ulist = Groups.get_users(group_id)
    members = [Users2.getUser(uid) for uid in ulist]
    return render_template("courseadmin_editgroup.html",
                           course=course,
                           group=group,
                           members=members)


@app.route("/cadmin/addgroup/<int:course_id>")
@require_course_perm("useradmin")
def cadmin_addgroup(course_id):
    """ Present a page for creating a group
    """
    course = Courses2.get_course(course_id)
    return render_template("courseadmin_addgroup.html", course=course)


@app.route("/cadmin/<int:course_id>/editgroup/<int:group_id>/addperson",
           methods=["POST", ])
@require_course_perm("useradmin")
def cadmin_editgroup_addperson(course_id, group_id):
    """ Add a person to the group.
    """
    group = None
    try:
        group = Groups.getInfo(group_id)
    except KeyError:
        abort(404)

    if not group:
        abort(404)

    if not "uname" in request.form:
        abort(400)

    new_uname = request.form['uname']
    try:
        new_uid = Users2.getUidByUname(new_uname)
    except KeyError:
        flash("User '%s' Not Found" % new_uname)
    else:
        if not new_uid:
            flash("User '%s' Not Found" % new_uname)
        else:
            Groups.add_user(new_uid, group_id)
            flash("Added '%s to group." % (new_uname,))

    return redirect(url_for('cadmin_editgroup',
                            course_id=course_id,
                            group_id=group_id))


@app.route("/cadmin/<int:course_id>/topics", methods=['GET', 'POST'])
@require_course_perm("questionedit")
def cadmin_edittopics(course_id):
    """ Present a page to view and edit all topics, including hidden. """
    course = None
    try:
        course = Courses2.get_course(course_id)
    except KeyError:
        abort(404)

    if not course:
        abort(404)

    topics = Courses2.get_topics_list(course_id)
    return render_template("courseadmin_edittopics.html",
                           course=course,
                           topics=topics)


@app.route("/cadmin/<int:course_id>/topics_save", methods=['POST'])
@require_course_perm("questionedit")
def cadmin_edittopics_save(course_id):
    """ Accept a submitted topics page and save it."""
    course = None
    try:
        course = Courses2.get_course(course_id)
    except KeyError:
        abort(404)

    if not course:
        abort(404)

    if "cancel" in request.form:
        flash("Changes Cancelled!")
        return redirect(url_for('cadmin_top', course_id=course_id))

    if CourseAdmin.do_topic_update(course, request):
        flash("Changes Saved!")
    else:
        flash("Error Saving!")
    return redirect(url_for('cadmin_edittopics', course_id=course_id))


@app.route("/cadmin/<int:course_id>/edittopic/<int:topic_id>")
@require_course_perm("questionedit")
def cadmin_edit_topic(course_id, topic_id):
    """ Present a page to view and edit a topic, including adding/editing
        questions and setting some parameters.
    """
    user_id = session['user_id']

    if not course_id:
        abort(404)

    course = Courses2.get_course(course_id)
    topic = {
        'id': topic_id,
        'position': Topics.get_pos(topic_id),
        'name': Topics.get_name(topic_id)
    }
    questions = [question
                 for question in Topics.get_qts(topic_id).values()]
    for question in questions:
        question['embed_id'] = DB.get_qt_embedid(question['id'])
        if question['embed_id']:
            question['embed_url'] = "%s/embed/question/%s/question.html" % \
                                    (OaConfig.parentURL, question['embed_id'])
        else:
            question['embed_url'] = None
        question['editor'] = DB.get_qt_editor(question['id'])

    all_courses = Courses2.get_course_list()
    all_courses = [cs
                   for cs in all_courses
                   if satisfyPerms(user_id, int(cs['id']),
                                   ("questionedit", "courseadmin",
                                    "sysadmin"))]
    all_courses.sort(lambda f, s: cmp(f['name'], s['name']))

    all_course_topics = []
    for cs in all_courses:
        topics = Courses.get_topics_all(cs['id'], numq=False)
        if topics:
            all_course_topics.append({'course': cs['name'], 'topics': topics})

    questions.sort(key=lambda k: k['position'])
    return render_template(
        "courseadmin_edittopic.html",
        course=course,
        topic=topic,
        questions=questions,
        all_course_topics=all_course_topics
    )


@app.route("/cadmin/<int:course_id>/topic/<int:topic_id>/<int:qt_id>/history")
@require_course_perm("courseadmin")
def cadmin_view_qtemplate_history(course_id, topic_id, qt_id):
    """ Show the practice history of the question template. """
    if not course_id:
        abort(404)

    course = Courses2.get_course(course_id)
    topic = {
        'id': topic_id,
        'position': Topics.get_pos(topic_id),
        'name': Topics.get_name(topic_id)
    }
    qtemplate = DB.get_qtemplate(qt_id)
    year = datetime.now().year
    years = range(year, year-6, -1)

    return render_template(
        "courseadmin_viewqtemplate.html",
        course=course,
        topic=topic,
        qtemplate=qtemplate,
        years=years
    )


@app.route("/cadmin/<int:course_id>/topic/<int:topic_id>")
@require_course_perm("courseadmin")
def cadmin_view_topic(course_id, topic_id):
    """ Present a page to view a topic, including basic stats """
    user_id = session['user_id']

    if not course_id:
        abort(404)

    course = Courses2.get_course(course_id)
    topic = {
        'id': topic_id,
        'position': Topics.get_pos(topic_id),
        'name': Topics.get_name(topic_id)
    }
    questions = [question for question in Topics.get_qts(topic_id).values()]
    for question in questions:
        question['embed_id'] = DB.get_qt_embedid(question['id'])
        if question['embed_id']:
            question['embed_url'] = "%s/embed/question/%s/question.html" % \
                                    (OaConfig.parentURL, question['embed_id'])
        else:
            question['embed_url'] = None
        question['editor'] = DB.get_qt_editor(question['id'])

    all_courses = Courses2.get_course_list()
    all_courses = [cs
                   for cs in all_courses
                   if satisfyPerms(user_id, int(cs['id']),
                                   ("questionedit", "courseadmin",
                                    "sysadmin"))]
    all_courses.sort(lambda f, s: cmp(f['name'], s['name']))

    all_course_topics = []
    for cs in all_courses:
        topics = Courses.get_topics_all(cs['id'], numq=False)
        if topics:
            all_course_topics.append({'course': cs['name'], 'topics': topics})

    questions.sort(key=lambda k: k['position'])
    return render_template(
        "courseadmin_viewtopic.html",
        course=course,
        topic=topic,
        questions=questions,
        all_course_topics=all_course_topics,
    )


@app.route("/cadmin/<int:course_id>/topic_save/<int:topic_id>",
           methods=['POST'])
@require_course_perm("questionedit")
def cadmin_topic_save(course_id, topic_id):
    """ Receive the page from cadmin_edit_topic and process any changes. """
    user_id = session['user_id']

    if not course_id:
        abort(404)

    if "cancel_edit" in request.form:
        flash("Topic Changes Cancelled!")
        return redirect(url_for('cadmin_top', course_id=course_id))

    if "save_changes" in request.form:
        result = Setup.doTopicPageCommands(request, topic_id, user_id)
        if result:
            # flash(result['mesg'])
            return redirect(url_for('cadmin_edit_topic', topic_id=topic_id))

    flash("Error saving Topic Information!")
    log(ERROR, "Error saving Topic Information " % repr(request.form))
    return redirect(url_for('cadmin_edit_topic', topic_id=topic_id))


@app.route("/cadmin/<int:course_id>/perms")
@require_course_perm("useradmin")
def cadmin_permissions(course_id):
    """ Present a page for them to assign permissions to the course"""
    course = Courses2.get_course(course_id)

    permlist = UserDB.getCoursePerms(course_id)
    perms = {}
    for uid, pid in permlist:  # (uid, permission)
        if not uid in perms:
            user = Users2.getUser(uid)
            perms[uid] = {
                'uname': user['uname'],
                'fullname': user['fullname'],
                'pids': []
            }
        perms[uid]['pids'].append(pid)

    return render_template(
        "courseadmin_permissions.html",
        perms=perms,
        course=course,
        pids=[5, 10, 14, 11, 8, 9, 15, 2]
    )


@app.route("/cadmin/<int:course_id>/perms_save", methods=["POST", ])
@require_course_perm("useradmin")
def cadmin_permissions_save(course_id):
    """ Present a page for them to save new permissions to the course """
    user_id = session['user_id']

    if "cancel" in request.form:
        flash("Permission changes cancelled")
        return redirect(url_for("cadmin_top", course_id=course_id))

    CourseAdmin.save_perms(request, course_id, user_id)
    flash("Changes saved")
    return redirect(url_for("cadmin_permissions", course_id=course_id))
