# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html


import os
import StringIO

from flask import render_template, session, \
    request, redirect, abort, url_for, flash, \
    send_file, Response
from logging import log, INFO

from .lib import UserAPI, OaDB, Topics, OaGeneral, Exams, Courses, \
    CourseAPI, OaSetup, OaAttachment, OaQEditor

MYPATH = os.path.dirname(__file__)

from .lib.Audit import audit, getRecordsByUser
from .lib.OaUserDB import checkPermission, satisfyPerms

from oasis import app, authenticated


# Does its own auth because it may be used in embedded questions
@app.route("/att/qatt/<int:qtemplate_id>/<int:version>/<int:variation>/<fname>")
def attachment_question(qtemplate_id, version, variation, fname):
    """ Serve the given question attachment """
    qt = OaDB.getQTemplate(qtemplate_id)
    if len(qt['embed_id']) < 1:  # if it's not embedded, check auth
        if 'user_id' not in session:
            session['redirect'] = request.path
            return redirect(url_for('index'))
    if OaAttachment.is_restricted(fname):
        abort(403)
    (mimetype, filename) = OaAttachment.getQuestionAttachmentDetails(qtemplate_id, version, variation, fname)
    if not mimetype:
        abort(404)

    return send_file(filename, mimetype)


@app.route("/att/qtatt/<int:qtemplate_id>/<int:version>/<int:variation>/<fname>")
# Does its own auth because it may be used in embedded questions
def attachment_qtemplate(qtemplate_id, version, variation, fname):
    """ Serve the given question attachment """
    qt = OaDB.getQTemplate(qtemplate_id)
    if len(qt['embed_id']) < 1:  # if it's not embedded, check auth
        if 'user_id' not in session:
            session['redirect'] = request.path
            return redirect(url_for('index'))
    (mimetype, filename) = OaAttachment.getQuestionAttachmentDetails(qtemplate_id, version, variation, fname)
    if OaAttachment.is_restricted(fname):
        abort(403)
    if not mimetype:
        abort(404)
    return send_file(filename, mimetype)


@app.route("/logout")
# doesn't need auth. sort of obviously.
def logout():
    """ Log the user out, if they're logged in. Mainly by clearing the session. """

    if "user_id" in session:
        user_id = session["user_id"]
        username = session["username"]
        session.pop("user_id")
        session.clear()
        audit(1, user_id, user_id, "UserAuth", "%s logged out" % username)
    return redirect(url_for('index'))


@app.errorhandler(401)
def custom_401(error):
    return Response('Authentication declined %s' % error, 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


@app.route("/login/webauth/flush")
def logout_and_flush():
    """ Called vi AJAX so the user doesn't see the interaction.
        We first send them an access declined to force them to send credentials.
        Then we accept those (invalid) credentials, which will flush the browser copy.
        Next time they access a page their credentials will be invalid so they'll have
        to re-login.
    """
    if not "logout" in session:
        # first hit, reject them
        session['logout'] = 1
        abort(401)

    # Job done, send them to start
    session.pop("logout")
    session.clear()
    return redirect(url_for("index"))


@app.route("/main/top")
@authenticated
def main_top():
    """ Present the top menu page """
    return render_template("main.html")


@app.route("/main/news")
@authenticated
def main_news():
    """ Present the top menu page """
    return render_template(
        "news.html",
        news=OaDB.getMessage("news"),
    )


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
        courses=OaSetup.getSortedCourseList()
    )


@app.route("/courseadmin/editquestion/<int:topic_id>/<int:qt_id>")
@authenticated
def qedit_redirect(topic_id, qt_id):
    """ Work out the appropriate question editor and redirect to it """
    etype = OaDB.getQTemplateEditor(qt_id)
    if etype == "Raw":
        return redirect(url_for("qedit_raw_edit", topic_id=topic_id, qt_id=qt_id))

    flash("Unknown Question Type, can't Edit")
    return redirect(url_for('cadmin_edit_topic', topic_id=topic_id))


@app.route("/qedit_raw/edit/<int:topic_id>/<int:qt_id>")
@authenticated
def qedit_raw_edit(topic_id, qt_id):
    """ Present a question editor so they can edit the question template.
        Main page of editor
    """
    user_id = session['user_id']

    course_id = Topics.getCourse(topic_id)

    if not (checkPermission(user_id, course_id, "OASIS_COURSECOORD")
            or checkPermission(user_id, course_id, "OASIS_COURSEADMIN")
            or checkPermission(user_id, course_id, "OASIS_QUESTIONEDITOR")
            or checkPermission(user_id, course_id, "OASIS_QUESTIONSOURCEVIEW")):
        flash("You do not have question editor privilege in this course")
        return redirect(url_for("cadmin_edit_topic", topic_id=topic_id))

    course = CourseAPI.getCourse(course_id)
    topic = Topics.getTopic(topic_id)
    qtemplate = OaDB.getQTemplate(qt_id)
    try:
        html = OaDB.getQTAttachment(qt_id, "qtemplate.html")
    except KeyError:
        try:
            html = OaDB.getQTAttachment(qt_id, "__qtemplate.html")
        except KeyError:
            html = "[question html goes here]"

    qtemplate['html'] = html
    attachnames = OaDB.getQTAttachments(qt_id, version=qtemplate['version'])
    attachments = [{'name': name,
                    'mimetype': OaDB.getQTAttachmentMimeType(qt_id, name)
                   } for name in attachnames if
                   not name in ['qtemplate.html', 'image.gif', 'datfile.txt', '__datfile.txt', '__qtemplate.html']]
    return render_template(
        "courseadmin_raw_edit.html",
        course=course,
        topic=topic,
        html=html,
        attachments=attachments,
        qtemplate=qtemplate
    )


@app.route("/qedit_raw/save/<int:topic_id>/<int:qt_id>", methods=['POST', ])
@authenticated
def qedit_raw_save(topic_id, qt_id):
    """ Accept the question editor form and save the results. """
    user_id = session['user_id']
    course_id = Topics.getCourse(topic_id)
    if not (checkPermission(user_id, course_id, "OASIS_COURSECOORD")
            or checkPermission(user_id, course_id, "OASIS_COURSEADMIN")
            or checkPermission(user_id, course_id, "OASIS_QUESTIONEDITOR")
            or checkPermission(user_id, course_id, "OASIS_QUESTIONSOURCEVIEW")):
        flash("You do not have question editor privilege in this course")
        return redirect(url_for("cadmin_edit_topic", topic_id=topic_id))

    form = request.form

    if 'cancel' in form:
        flash("Question editing cancelled, changes not saved.")
        return redirect(url_for("cadmin_edit_topic", topic_id=topic_id))

    version = OaDB.incrementQTVersion(qt_id)
    owner = UserAPI.getUser(user_id)
    OaDB.updateQTemplateOwner(qt_id, user_id)
    audit(3, user_id, qt_id, "qeditor",
          "version=%s,message=%s" % (version, "Edited: ownership set to %s" % owner['uname']))

    if 'qtitle' in form:
        qtitle = form['qtitle']
        qtitle = qtitle.replace("'", "&#039;")
        title = qtitle.replace("%", "&#037;")
        OaDB.updateQTemplateTitle(qt_id, title)

    if 'embed_id' in form:
        embed_id = form['embed_id']
        embed_id = ''.join([ch for ch in embed_id
                            if ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"])
        if not OaDB.updateQTemplateEmbedID(qt_id, embed_id):
            flash("Error updating EmbedID, possibly the value is already used elsewhere.")

    # They entered something into the html field and didn't upload a qtemplate.html
    if not ('newattachmentname' in form and form['newattachmentname'] == "qtemplate.html"):
        if 'newhtml' in form:
            html = form['newhtml'].encode("utf8")
            OaDB.createQTAttachment(qt_id, "qtemplate.html", "text/plain", html, version)

    # They uploaded a new qtemplate.html
    if 'newindex' in request.files:
        data = request.files['newindex'].read()
        if len(data) > 1:
            html = data.decode("utf8")
            OaDB.createQTAttachment(qt_id, "qtemplate.html", "text/plain", html, version)

    # They uploaded a new datfile
    if 'newdatfile' in request.files:
        data = request.files['newdatfile'].read()
        if len(data) > 1:
            df = data.decode("utf8")
            OaDB.createQTAttachment(qt_id, "datfile.txt", "text/plain", df, version)
            qvars = OaQEditor.parseDatfile(df)
            for row in range(0, len(qvars)):
                OaDB.addQTVariation(qt_id, row + 1, qvars[row], version)

                # They uploaded a new image file
    if 'newimgfile' in request.files:
        data = request.files['newimgfile'].read()
        if len(data) > 1:
            df = data.decode("utf8")
            OaDB.createQTAttachment(qt_id, "image.gif", "image/gif", df, version)

    if 'newmodule' in form:
        try:
            newmodule = int(form['newmodule'])
        except (ValueError, TypeError):
            flash(form['newmodule'])
            pass
        else:
            OaDB.updateQTemplateMarker(qt_id, newmodule)

    if 'newmaxscore' in form:
        try:
            newmaxscore = float(form['newmaxscore'])
        except (ValueError, TypeError):
            newmaxscore = None
        OaDB.updateQTemplateMaxScore(qt_id, newmaxscore)

    newname = False
    if 'newattachmentname' in form:
        if len(form['newattachmentname']) > 1:
            newname = form['newattachmentname']
    if 'newattachment' in request.files:
        f = request.files['newattachment']
        if not newname:  # If they haven't supplied a filename we'll use the name of the file they uploaded
            newname = f.filename
        data = f.read()
        mtype = f.content_type
        OaDB.createQTAttachment(qt_id, newname, mtype, data, version)
        log(INFO, "File '%s' uploaded by %s" % (newname, session['username']))

    flash("Question changes saved")
    return redirect(url_for("qedit_raw_edit", topic_id=topic_id, qt_id=qt_id))


@app.route("/qedit_raw/att/<int:qt_id>/<fname>")
@authenticated
def qedit_raw_attach(qt_id, fname):
    """ Serve the given question template attachment straight from DB so it's fresh """
    mimetype = OaDB.getQTAttachmentMimeType(qt_id, fname)
    data = OaDB.getQTAttachment(qt_id, fname)
    if not data:
        abort(404)
    if not mimetype:
        mimetype = "text/plain"
    if mimetype == "text/html":
        mimetype = "text/plain"
    sIO = StringIO.StringIO(data)
    return send_file(sIO, mimetype, as_attachment=True, attachment_filename=fname)


@app.route("/setup/usercreate", methods=['POST', 'GET'])
@authenticated
def setup_usercreate():
    """ Show a page allowing the admin to enter user details to create an account. """
    user_id = session['user_id']

    if not checkPermission(user_id, -1, "OASIS_USERADMIN"):
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
            if 'new_uname' in form:
                new_uname = form['new_uname']
            if 'new_fname' in form:
                new_fname = form['new_fname']
            if 'new_sname' in form:
                new_sname = form['new_sname']
            if 'new_email' in form:
                new_email = form['new_email']
            if 'new_pass' in form:
                new_pass = form['new_pass']
            if 'new_confirm' in form:
                new_confirm = form['new_confirm']

            if not all((new_uname, new_email, new_pass, new_confirm)):
                error = "Please fill in all fields."

            elif UserAPI.getUidByUname(new_uname):
                error = "ERROR: An account already exists with that name"

            elif new_confirm == "" or not new_confirm == new_pass:
                error = "Passwords don't match (or are empty)"
            else:   # yaay, it's ok
                # uname, passwd, givenname, familyname, acctstatus, studentid, email=None, expiry=None, source="local"
                UserAPI.create(new_uname, "nologin-creation", new_fname, new_sname, 2, '', new_email)
                UserAPI.setPassword(UserAPI.getUidByUname(new_uname), new_pass)
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

    if not checkPermission(user_id, -1, "OASIS_USERADMIN"):
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
                uids = UserAPI.find(needle)
                users = [UserAPI.getUser(uid) for uid in uids]
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

    if not checkPermission(user_id, -1, "OASIS_USERADMIN"):
        flash("You do not have User Administration access.")
        return redirect(url_for('setup_top'))

    user = UserAPI.getUser(audit_id)
    audits = getRecordsByUser(audit_id)
    for aud in audits:
        aud['humantime'] = OaGeneral.humanDate(aud['time'])
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

    if not checkPermission(user_id, -1, "OASIS_USERADMIN"):
        flash("You do not have User Administration access.")
        return redirect(url_for('setup_top'))

    user = UserAPI.getUser(view_id)
    examids = Exams.getExamsDone(view_id)
    exams = []
    for examid in examids:
        exam = Exams.getExamStruct(examid)
        started = OaGeneral.humanDate(exam['start'])
        exam['started'] = started

        if satisfyPerms(user_id, exam['cid'], ("OASIS_VIEWMARKS", )):
            exam['viewable'] = True
        else:
            exam['viewable'] = False

        exams.append(exam)
    exams.sort(key=lambda x: x['start_epoch'], reverse=True)

    course_ids = UserAPI.getCourses(view_id)
    courses = []
    for course_id in course_ids:
        courses.append(CourseAPI.getCourse(course_id))
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

    user = UserAPI.getUser(user_id)
#    examids = Exams.getExamsDone(user_id)
#    exams = []
#   for examid in examids:
#        exam = Exams.getExamStruct(examid)
#        started = OaGeneral.humanDate(exam['start'])
#        exam['started'] = started

#        if satisfyPerms(user_id, exam['cid'], ("OASIS_VIEWMARKS", )):
#           exam['viewable'] = True
#        else:
#            exam['viewable'] = False

#        exams.append(exam)
#    exams.sort(key=lambda x: x['start_epoch'], reverse=True)

    course_ids = UserAPI.getCourses(user_id)
    courses = []
    for course_id in course_ids:
        courses.append(CourseAPI.getCourse(course_id))
    return render_template(
        'setup_myprofile.html',
        user=user,
#        exams=exams,
        courses=courses
    )


@app.route("/setup/changepass")
@authenticated
def setup_change_pass():
    """ Ask for a new password """
    user_id = session['user_id']

    user = UserAPI.getUser(user_id)
    return render_template(
        'setup_changepassword.html',
        user=user,
    )


@app.route("/setup/changepass_submit", methods=["POST",])
@authenticated
def setup_change_pass_submit():
    """ Set a new password """
    user_id = session['user_id']

    user = UserAPI.getUser(user_id)

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

    UserAPI.setPassword(user_id=user_id, clearpass=newpass)
    audit(1, user_id, user_id, "Setup", "%s reset password for %s." % (user['uname'], user['uname']))
    flash("Password changed")
    return redirect(url_for("setup_myprofile"))


@app.route("/admin/top")
@authenticated
def admin_top():
    """ Present the top level admin page """
    return render_template(
        "admintop.html",
        courses=OaSetup.getSortedCourseList()
    )


@app.route("/admin/courses")
@authenticated
def admin_courses():
    """ Present page to administer courses in the system """
    user_id = session['user_id']
    if not checkPermission(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))
    courses = OaSetup.getSortedCourseList(with_stats=True, only_active=False)

    return render_template(
        "admin_courselist.html",
        courses=courses
    )


@app.route("/admin/course/<int:course_id>")
@authenticated
def admin_course(course_id):
    """ Present page to administer settings for a given course"""
    user_id = session['user_id']
    if not checkPermission(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))

    course = CourseAPI.getCourse(course_id)
    course['size'] = len(Courses.getUsersInCourse(course_id))
    return render_template(
        "admin_course.html",
        course=course
    )


@app.route("/admin/add_course")
@authenticated
def admin_add_course():
    """ Present page to administer settings for a given course """
    user_id = session['user_id']
    if not checkPermission(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))
    course = {'course_name': '',
              'course_title': '',
              'active': True
    }
    return render_template(
        "admin_add_course.html",
        course=course
    )


@app.route("/admin/course/save/<int:course_id>", methods=['POST',])
@authenticated
def admin_course_save(course_id):
    """ accept saved settings """
    user_id = session['user_id']
    if not checkPermission(user_id, 0, "OASIS_SYSADMIN"):
        flash("You do not have system administrator permission")
        return redirect(url_for('setup_top'))

    form = request.form
    if 'cancel_edit' in form:
        flash("Course edits cancelled")
        return redirect(url_for("admin_courses"))

    if not 'save_changes' in form:
        abort(400)

    changed = False
    course = CourseAPI.getCourse(course_id)
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
            enrol_freq = int(float(enrol_freq)*60)  # form says hours, we want minutes.
            Courses.setEnrolFreq(course_id, enrol_freq)

    if changed:
        CourseAPI.reloadCoursesIfNeeded()
        flash("Course changes saved!")
        return redirect(url_for("admin_courses"))
    course = CourseAPI.getCourse(course_id)
    course['size'] = len(Courses.getUsersInCourse(course_id))
    return render_template(
        "admin_course.html",
        course=course
    )


@app.route("/admin/add_course/save", methods=['POST',])
@authenticated
def admin_add_course_save():
    """ accept saved settings for a new course"""
    user_id = session['user_id']
    if not checkPermission(user_id, 0, "OASIS_SYSADMIN"):
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

    CourseAPI.reloadCoursesIfNeeded()
    flash("Course %s added!" % name )
    course = CourseAPI.getCourse(course_id)
    course['size'] = 0
    return render_template(
        "admin_course.html",
        course=course
    )
