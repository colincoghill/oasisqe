# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" UI for various setup options. Changing password, profile, user creation.
"""

import os

from flask import render_template, session, \
    request, redirect, url_for, flash

from .lib import Users2, General, Exams, \
    Courses2, Setup

MYPATH = os.path.dirname(__file__)

from .lib.Audit import audit, get_records_by_user
from .lib.Permissions import check_perm, satisfyPerms

from oasis import app, authenticated


@app.route("/setup/top")
@authenticated
def setup_top():
    """ Present the top menu page"""
    return render_template("setuptop.html")


@app.route("/setup/courses")
@authenticated
def setup_courses():
    """ Let the user choose a course to administer """
    return render_template(
        "setupchoosecourse.html",
        courses=Setup.get_sorted_courselist()
    )


@app.route("/setup/usercreate", methods=['POST', 'GET'])
@authenticated
def setup_usercreate():
    """ Show a page allowing the admin to enter user details
        to create an account.
    """
    user_id = session['user_id']

    if not check_perm(user_id, -1, "useradmin"):
        flash("You do not have User Administration access.")
        return redirect(url_for('setup_top'))

    new_uname = ""
    new_fname = ""
    new_sname = ""
    new_email = ""
    new_pass = ""
    new_confirm = ""
    error = None

    if request.method == "POST":
        form = request.form

        if "usercreate_cancel" in form:
            flash("User Account Creation Cancelled")
            return redirect(url_for('setup_usersearch'))

        if "usercreate_save" in form:
            new_uname = form.get('new_uname', "")
            new_fname = form.get('new_fname', "")
            new_sname = form.get('new_sname', "")
            new_email = form.get('new_email', "")
            new_pass = form.get('new_pass', "")
            new_confirm = form.get('new_confirm', "")

            if not all((new_uname, new_email, new_pass, new_confirm)):
                error = "Please fill in all fields."

            elif Users2.getUidByUname(new_uname):
                error = "ERROR: An account already exists with that name"

            elif new_confirm == "" or not new_confirm == new_pass:
                error = "Passwords don't match (or are empty)"
            else:   # yaay, it's ok
                # uname, passwd, givenname, familyname, acctstatus,
                # studentid, email=None, expiry=None, source="local"
                Users2.create(new_uname,
                              "nologin-creation",
                              new_fname,
                              new_sname,
                              2,
                              '',
                              new_email)
                Users2.setPassword(Users2.getUidByUname(new_uname), new_pass)
                flash("New User Account Created for %s" % new_uname)
                new_uname = ""
                new_fname = ""
                new_sname = ""
                new_email = ""
                new_pass = ""
                new_confirm = ""

    if error:
        flash(error)
    return render_template(
        'setup_usercreate.html',
        new_uname=new_uname,
        new_fname=new_fname,
        new_sname=new_sname,
        new_email=new_email,
        new_pass=new_pass,
        new_confirm=new_confirm
    )


@app.route("/setup/usersearch", methods=['POST', 'GET'])
@authenticated
def setup_usersearch():
    """ Show a page allowing the admin search for users, or create new ones"""
    user_id = session['user_id']

    if not check_perm(user_id, -1, "useradmin"):
        flash("You do not have User Administration access.")
        return redirect(url_for('setup_top'))

    users = []
    nonefound = False
    if request.method == "POST":
        if 'usersearch_name' in request.form:
            needle = request.form['usersearch_name']

            if len(needle) < 2:
                flash("Search term too short, please try something longer")
            else:
                uids = Users2.find(needle)
                users = [Users2.get_user(uid) for uid in uids]
                if len(users) == 0:
                    nonefound = True
                else:
                    users.sort(key=lambda x: x['uname'])

    return render_template(
        'setup_usersearch.html',
        users=users,
        nonefound=nonefound
    )


@app.route("/setup/useraudit/<int:audit_id>")
@authenticated
def setup_useraudit(audit_id):
    """ Show all the audit entries for the given user account. """
    user_id = session['user_id']

    if not check_perm(user_id, -1, "useradmin"):
        flash("You do not have User Administration access.")
        return redirect(url_for('setup_top'))

    user = Users2.get_user(audit_id)
    audits = get_records_by_user(audit_id)
    for aud in audits:
        aud['humantime'] = General.humanDate(aud['time'])
    return render_template(
        'setup_useraudit.html',
        user=user,
        audits=audits
    )


@app.route("/setup/userview/<int:view_id>")
@authenticated
def setup_usersummary(view_id):
    """ Show an account summary for the given user account. """
    user_id = session['user_id']

    if not check_perm(user_id, -1, "useradmin"):
        flash("You do not have User Administration access.")
        return redirect(url_for('setup_top'))

    user = Users2.get_user(view_id)
    examids = Exams.get_exams_done(view_id)
    exams = []
    for examid in examids:
        exam = Exams.get_exam_struct(examid)
        started = General.humanDate(exam['start'])
        exam['started'] = started

        exam['viewable'] = satisfyPerms(user_id, exam['cid'], ("viewmarks", ))

        exams.append(exam)
    exams.sort(key=lambda x: x['start_epoch'], reverse=True)

    course_ids = Users2.getCourses(view_id)
    courses = []
    for course_id in course_ids:
        courses.append(Courses2.get_course(course_id))
    return render_template(
        'setup_usersummary.html',
        user=user,
        exams=exams,
        courses=courses
    )


@app.route("/setup/myprofile")
@authenticated
def setup_myprofile():
    """ Show an account summary for the current user account. """
    user_id = session['user_id']

    user = Users2.get_user(user_id)
#    examids = Exams.getExamsDone(user_id)
#    exams = []
#   for examid in examids:
#        exam = Exams.getExamStruct(examid)
#        started = OaGeneral.humanDate(exam['start'])
#        exam['started'] = started

#        if satisfyPerms(user_id, exam['cid'], ("viewmarks", )):
#           exam['viewable'] = True
#        else:
#            exam['viewable'] = False

#        exams.append(exam)
#    exams.sort(key=lambda x: x['start_epoch'], reverse=True)

    course_ids = Users2.getCourses(user_id)
    courses = []
    for course_id in course_ids:
        courses.append(Courses2.get_course(course_id))
    return render_template(
        'setup_myprofile.html',
        user=user,
        courses=courses
        # exams=exams
    )


@app.route("/setup/changepass")
@authenticated
def setup_change_pass():
    """ Ask for a new password """
    user_id = session['user_id']

    user = Users2.get_user(user_id)
    return render_template(
        'setup_changepassword.html',
        user=user,
    )


@app.route("/setup/changepass_submit", methods=["POST", ])
@authenticated
def setup_change_pass_submit():
    """ Set a new password """
    user_id = session['user_id']

    user = Users2.get_user(user_id)

    if not "newpass" in request.form or not "confirm" in request.form:
        flash("Please provide your new password")
        return redirect(url_for("setup_change_pass"))

    newpass = request.form['newpass']
    confirm = request.form['confirm']

    if len(newpass) < 7:
        flash("Password is too short, please try something longer.")
        return redirect(url_for("setup_change_pass"))

    if not newpass == confirm:
        flash("Passwords do not match")
        return redirect(url_for("setup_change_pass"))

    Users2.setPassword(user_id=user_id, clearpass=newpass)
    audit(1, user_id,
          user_id,
          "Setup", "%s reset password for %s." % (user['uname'], user['uname']))
    flash("Password changed")
    return redirect(url_for("setup_myprofile"))
