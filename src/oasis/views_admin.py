# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html


import os
import datetime

from flask import render_template, session, \
    request, redirect, abort, url_for, flash

from .lib import Courses, Courses2, Setup, Periods, Feeds

MYPATH = os.path.dirname(__file__)
from .lib.UserDB import check_perm
from .lib import DB, Groups
from oasis import app, authenticated


@app.route("/admin/top")
@authenticated
def admin_top():
    """ Present the top level admin page """
    db_version = DB.getDBVersion()
    return render_template(
        "admintop.html",
        courses=Setup.get_sorted_courselist(),
        db_version = db_version
    )


@app.route("/admin/courses")
@authenticated
def admin_courses():
    """ Present page to administer courses in the system """
    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))
    courses = Setup.get_sorted_courselist(with_stats=True, only_active=False)

    return render_template(
        "admin_courselist.html",
        courses=courses
    )


@app.route("/admin/enrol/top")
@authenticated
def admin_enrol_top():
    """ Present menu page of enrolment related options """
    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))

    return render_template(
        "admin_enrol_top.html"
    )


@app.route("/admin/feeds")
@authenticated
def admin_feeds():
    """ Present menu page of enrolment related options """
    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))

    return render_template(
        "admin_group_feeds.html"
    )


@app.route("/admin/periods")
@authenticated
def admin_periods():
    """ Present page to administer time periods in the system """
    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))
    periods = Periods.all_list()

    return render_template(
        "admin_periods.html",
        periods=periods
    )


@app.route("/admin/edit_period/<int:p_id>")
@authenticated
def admin_edit_period(p_id):
    """ Present page to edit a time period in the system """
    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))
    try:
        period = Periods.Period(id=p_id)
    except KeyError:
        abort(404)
    else:
        period.start_date = period.start.strftime("%a %d %b %Y")
        period.finish_date = period.finish.strftime("%a %d %b %Y")
    return render_template(
        "admin_editperiod.html",
        period=period
    )


@app.route("/admin/edit_feed/<int:feed_id>")
@authenticated
def admin_edit_feed(feed_id):
    """ Present page to edit a feed in the system """
    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))
    try:
        feed = Feeds.Feed(id=feed_id)
    except KeyError:
        abort(404)
    return render_template(
        "admin_edit_group_feed.html",
        feed=feed
    )


@app.route("/admin/add_feed")
@authenticated
def admin_add_feed():
    """ Present page to add a feed to the system """
    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))

    return render_template(
        "admin_edit_group_feed.html",
        feed = {'id':0}
    )


@app.route("/admin/add_period")
@authenticated
def admin_add_period():
    """ Present page to add a time period in the system """
    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))

    return render_template(
        "admin_editperiod.html",
        period = {'id':0}
    )


@app.route("/admin/edit_period_submit/<int:p_id>", methods=["POST",])
@authenticated
def admin_edit_period_submit(p_id):
    """ Submit edit period form """
    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))

    if "cancel" in request.form:
        flash("Edit cancelled!")
        return redirect(url_for("admin_periods"))

    try:
        start = datetime.datetime.strptime(request.form['start'], "%a %d %b %Y")
    except ValueError:
        start = None

    try:
        finish = datetime.datetime.strptime(request.form['finish'], "%a %d %b %Y")
    except ValueError:
        finish = None

    name = request.form['name']
    title = request.form['title']
    code = request.form['code']
    if start:
        start_date = start.strftime("%a %d %b %Y")
    else:
        start_date = ""
    if finish:
        finish_date = finish.strftime("%a %d %b %Y")
    else:
        finish_date = ""

    if p_id == 0:  # It's a new one being created
        period = Periods.Period(
            id=0,
            name=name,
            title=title,
            code=code,
            start=start,
            finish=finish
        )
    else:
        try:
            period = Periods.Period(id=p_id)
        except KeyError:
            abort(404)

    period.id = p_id
    period.start = start
    period.finish = finish
    period.name = request.form['name']
    period.title = request.form['title']
    period.code = request.form['code']
    period.start_date = start_date
    period.finish_date = finish_date

    if not start:
        flash("Can't Save: can't understand start date.")
        return render_template(
            "admin_editperiod.html",
            period=period
        )

    if not finish:
        flash("Can't Save: can't understand finish date.")
        return render_template(
            "admin_editperiod.html",
            period=period
        )

    if name == "":
        flash("Can't Save: Name must be supplied")
        return render_template(
            "admin_editperiod.html",
            period=period
        )

    if not period.editable():
        flash("That time period is not editable!")
        return redirect(url_for("admin_periods"))

    try:
        period.save()
    except ValueError, err:  # Probably a duplicate or something
        flash("Can't Save: %s" % err)
        return render_template(
            "admin_editperiod.html",
            period=period
        )
    flash("Changes saved", category='success')
    return redirect(url_for("admin_periods"))


@app.route("/admin/course/<int:course_id>")
@authenticated
def admin_course(course_id):
    """ Present page to administer settings for a given course"""
    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))

    course = Courses2.get_course(course_id)
    course['size'] = len(Courses.getUsersInCourse(course_id))

    groups = [Groups.getInfo(group_id)
              for group_id in Courses.get_groups(course_id)]

    for group in groups:
        if not group['enddate']:
            group['enddate'] = "-"
        elif group['enddate'] > datetime.datetime(year=9990, month=1, day=1):
            group['enddate'] = "-"

        if group['startdate']:
            group['startdate'] = group['startdate'].strftime("%d %b %Y")
        else:
            group['startdate'] = "-"
        group['size'] = len(Groups.get_users(group['id']))

    allgroups = Groups.getInfoAll()
    return render_template(
        "admin_course.html",
        course=course,
        groups=groups,
        allgroups=allgroups
    )


@app.route("/admin/add_course")
@authenticated
def admin_add_course():
    """ Present page to administer settings for a given course """
    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))
    course = {
        'course_name': '',
        'course_title': '',
        'active': True
    }
    return render_template(
        "admin_add_course.html",
        course=course
    )


@app.route("/admin/course/save/<int:course_id>", methods=['POST', ])
@authenticated
def admin_course_save(course_id):
    """ accept saved settings """
    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))

    form = request.form
    if 'cancel_edit' in form:
        flash("Course edits cancelled")
        return redirect(url_for("admin_courses"))

    if not 'save_changes' in form:
        abort(400)

    changed = False
    course = Courses2.get_course(course_id)
    if 'course_name' in form:
        name = form['course_name']
        if not name == course['name']:
            changed = True
            Courses.setName(course_id, name)

    if 'course_title' in form:
        title = form['course_title']
        if not title == course['title']:
            changed = True
            Courses.setTitle(course_id, title)

    if 'course_active' in form:
        active = form['course_active']
        if active == '1' or active == 1:
            active = True
        else:
            active = False
        if not (active == course['active']):
            changed = True
            Courses.setActive(course_id, active)

    if 'enrol_type' in form:
        enrol_type = form['enrol_type']
        if not (enrol_type == course['enrol_type']):
            changed = True
            Courses.setEnrolType(course_id, enrol_type)

    if 'registration' in form:
        registration = form['registration']
        if not (registration == course['registration']):
            changed = True
            Courses.setRegistration(course_id, registration)

    if 'enrol_location' in form:
        enrol_location = form['enrol_location']
        if not (enrol_location == course['enrol_location']):
            changed = True
            Courses.setEnrolLocation(course_id, enrol_location)

    if 'enrol_freq' in form:
        enrol_freq = form['enrol_freq']
        if not (enrol_freq == course['enrol_freq']):
            changed = True
            # form says hours, we want minutes.
            enrol_freq = int(float(enrol_freq) * 60)
            Courses.setEnrolFreq(course_id, enrol_freq)

    if changed:
        Courses2.reloadCoursesIfNeeded()
        flash("Course changes saved!")
        return redirect(url_for("admin_courses"))
    course = Courses2.get_course(course_id)
    course['size'] = len(Courses.getUsersInCourse(course_id))
    return render_template(
        "admin_course.html",
        course=course
    )


@app.route("/admin/add_course/save", methods=['POST', ])
@authenticated
def admin_add_course_save():
    """ accept saved settings for a new course"""

    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))

    form = request.form
    if 'cancel_edit' in form:
        flash("Course creation cancelled")
        return redirect(url_for("admin_courses"))

    if not 'save_changes' in form:
        abort(400)

    if not 'course_name' in form:
        flash("You must give the course a name!")
        return redirect(url_for("admin_add_course"))

    if not 'course_title' in form:
        flash("You must give the course a title!")
        return redirect(url_for("admin_add_course"))

    name = form['course_name']
    title = form['course_title']

    if len(name) < 1:
        flash("You must give the course a name!")
        return redirect(url_for("admin_add_course"))

    if len(title) < 1:
        flash("You must give the course a title!")
        return redirect(url_for("admin_add_course"))

    course_id = Courses.create(name, title, user_id, 1)
    if not course_id:
        flash("Error Adding Course!")
        return redirect(url_for("admin_add_course"))

    if 'course_active' in form:
        active = form['course_active']
        if active == '1' or active == 1:
            active = True
        else:
            active = False
        Courses.setActive(course_id, active)

    Courses2.reloadCoursesIfNeeded()
    flash("Course %s added!" % name)
    course = Courses2.get_course(course_id)
    course['size'] = 0
    return render_template(
        "admin_course.html",
        course=course
    )


@app.route("/admin/edit_messages")
@authenticated
def admin_editmessages():
    """ Present page to administer messages in the system """

    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))
    mesg_news = DB.getMessage("news")
    mesg_login = DB.getMessage("loginmotd")
    return render_template(
        "admin_editmessages.html",
        mesg_news = mesg_news,
        mesg_login = mesg_login
    )


@app.route("/admin/save_messages",
           methods=["POST", ])
@authenticated
def admin_savemessages():
    """ Save messages in the system """

    user_id = session['user_id']
    if not check_perm(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))

    form = request.form
    if 'cancel' in form:
        flash("Changes Cancelled")
        return redirect(url_for("admin_top"))

    if 'mesg_news' in form:
        DB.setMessage("news", form['mesg_news'])
    if 'mesg_news' in form:
        DB.setMessage("loginmotd", form['mesg_login'])
    flash("Changes saved")
    return redirect(url_for("admin_top"))