# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Miscellaneous UI functions.

"""

import os
import StringIO
import datetime

from flask import render_template, session, \
    request, redirect, abort, url_for, flash, \
    send_file, Response
from logging import log, INFO

from .lib import Users2, DB, Topics, \
    Courses2, Attach, QEditor

MYPATH = os.path.dirname(__file__)

from .lib.Audit import audit
from .lib.Permissions import check_perm

from oasis import app, authenticated


# Does its own auth because it may be used in embedded questions
@app.route("/att/qatt/<int:qt_id>/<int:version>/<int:variation>/<fname>")
def attachment_question(qt_id, version, variation, fname):
    """ Serve the given question attachment """
    qtemplate = DB.get_qtemplate(qt_id)
    if len(qtemplate['embed_id']) < 1:  # if it's not embedded, check auth
        if 'user_id' not in session:
            session['redirect'] = request.path
            return redirect(url_for('index'))
    if Attach.is_restricted(fname):
        abort(403)
    (mtype, fname) = Attach.q_att_details(qt_id, version, variation, fname)
    if not mtype:
        abort(404)

    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(10)
    response = send_file(fname, mtype)
    response.headers["Expires"] = expiry_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return response


@app.route("/att/qtatt/<int:qt_id>/<int:version>/<int:variation>/<fname>")
# Does its own auth because it may be used in embedded questions
def attachment_qtemplate(qt_id, version, variation, fname):
    """ Serve the given question attachment """
    qtemplate = DB.get_qtemplate(qt_id)
    if len(qtemplate['embed_id']) < 1:  # if it's not embedded, check auth
        if 'user_id' not in session:
            session['redirect'] = request.path
            return redirect(url_for('index'))
    (mtype, filename) = Attach.q_att_details(qt_id, version, variation, fname)
    if Attach.is_restricted(fname):
        abort(403)
    if not mtype:
        abort(404)
    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(10)
    response = send_file(filename, mtype)
    response.headers["Expires"] = expiry_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return response


@app.route("/logout")
# doesn't need auth. sort of obviously.
def logout():
    """ Log the user out, if they're logged in. Mainly by clearing the session.
    """

    if "user_id" in session:
        user_id = session["user_id"]
        username = session["username"]
        session.pop("user_id")
        session.clear()
        audit(1, user_id, user_id, "UserAuth", "%s logged out" % username)
    return redirect(url_for('index'))


@app.errorhandler(401)
def custom_401(error):
    """ Give them a custom 401 error
    """
    return Response('Authentication declined %s' % error,
                    401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})


@app.route("/login/webauth/flush")
def logout_and_flush():
    """ Called vi AJAX so the user doesn't see the interaction.
        We first send them an access declined to force them to send credentials.
        Then we accept those (invalid) credentials, which will flush the browser
        copy. Next time they access a page their credentials will be
        invalid so they'll have to re-login.
    """
    if "logout" not in session:
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
        news=DB.get_message("news"),
    )


@app.route("/cadmin/<int:course_id>/editquestion/<int:topic_id>/<int:qt_id>")
@authenticated
def qedit_redirect(course_id, topic_id, qt_id):
    """ Work out the appropriate question editor and redirect to it """
    etype = DB.get_qt_editor(qt_id)
    if etype == "Raw":
        return redirect(url_for("qedit_raw_edit",
                                topic_id=topic_id,
                                qt_id=qt_id))

    flash("Unknown Question Type, can't Edit")
    return redirect(url_for('cadmin_edit_topic',
                            course_id=course_id,
                            topic_id=topic_id))


@app.route("/qedit_raw/edit/<int:topic_id>/<int:qt_id>")
@authenticated
def qedit_raw_edit(topic_id, qt_id):
    """ Present a question editor so they can edit the question template.
        Main page of editor
    """
    user_id = session['user_id']

    course_id = Topics.get_course_id(topic_id)

    if not (check_perm(user_id, course_id, "courseadmin")
            or check_perm(user_id, course_id, "courseadmin")
            or check_perm(user_id, course_id, "questionedit")
            or check_perm(user_id, course_id, "questionsource")):
        flash("You do not have question editor privilege in this course")
        return redirect(url_for("cadmin_edit_topic",
                                course_id=course_id, topic_id=topic_id))

    course = Courses2.get_course(course_id)
    topic = Topics.get_topic(topic_id)
    qtemplate = DB.get_qtemplate(qt_id)
    try:
        html = DB.get_qt_att(qt_id, "qtemplate.html")
    except KeyError:
        try:
            html = DB.get_qt_att(qt_id, "__qtemplate.html")
        except KeyError:
            html = "[question html goes here]"

    qtemplate['html'] = html
    attachnames = DB.get_qt_atts(qt_id, version=qtemplate['version'])
    attachments = [
        {
            'name': name,
            'mimetype': DB.get_qt_att_mimetype(qt_id, name)
        } for name in attachnames
        if name not in ['qtemplate.html', 'image.gif', 'datfile.txt',
                        '__datfile.txt', '__qtemplate.html']
    ]
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
    valid = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    user_id = session['user_id']
    course_id = Topics.get_course_id(topic_id)
    if not (check_perm(user_id, course_id, "courseadmin")
            or check_perm(user_id, course_id, "courseadmin")
            or check_perm(user_id, course_id, "questionedit")
            or check_perm(user_id, course_id, "questionsource")):
        flash("You do not have question editor privilege in this course")
        return redirect(url_for("cadmin_edit_topic",
                                course_id=course_id,
                                topic_id=topic_id))

    form = request.form

    if 'cancel' in form:
        flash("Question editing cancelled, changes not saved.")
        return redirect(url_for("cadmin_edit_topic",
                                course_id=course_id,
                                topic_id=topic_id))

    version = DB.incr_qt_version(qt_id)
    owner = Users2.get_user(user_id)
    DB.update_qt_owner(qt_id, user_id)
    audit(3, user_id, qt_id, "qeditor",
          "version=%s,message=%s" %
          (version, "Edited: ownership set to %s" % owner['uname']))

    if 'qtitle' in form:
        qtitle = form['qtitle']
        qtitle = qtitle.replace("'", "&#039;")
        title = qtitle.replace("%", "&#037;")
        DB.update_qt_title(qt_id, title)

    if 'embed_id' in form:
        embed_id = form['embed_id']
        embed_id = ''.join([ch for ch in embed_id
                            if ch in valid])
        if not DB.update_qt_embedid(qt_id, embed_id):
            flash("Error updating EmbedID, "
                  "possibly the value is already used elsewhere.")

    # They entered something into the html field and didn't upload a
    # qtemplate.html
    if not ('newattachmentname' in form
            and form['newattachmentname'] == "qtemplate.html"):
        if 'newhtml' in form:
            html = form['newhtml'].encode("utf8")
            DB.create_qt_att(qt_id,
                             "qtemplate.html",
                             "text/plain",
                             html,
                             version)

    # They uploaded a new qtemplate.html
    if 'newindex' in request.files:
        data = request.files['newindex'].read()
        if len(data) > 1:
            html = data
            DB.create_qt_att(qt_id,
                             "qtemplate.html",
                             "text/plain",
                             html,
                             version)

    # They uploaded a new datfile
    if 'newdatfile' in request.files:
        data = request.files['newdatfile'].read()
        if len(data) > 1:
            DB.create_qt_att(qt_id,
                             "datfile.txt",
                             "text/plain",
                             data,
                             version)
            qvars = QEditor.parse_datfile(data)
            for row in range(0, len(qvars)):
                DB.add_qt_variation(qt_id, row + 1, qvars[row], version)

                # They uploaded a new image file
    if 'newimgfile' in request.files:
        data = request.files['newimgfile'].read()
        if len(data) > 1:
            df = data
            DB.create_qt_att(qt_id, "image.gif", "image/gif", df, version)

    if 'newmodule' in form:
        try:
            newmodule = int(form['newmodule'])
        except (ValueError, TypeError):
            flash(form['newmodule'])
        else:
            DB.update_qt_marker(qt_id, newmodule)

    if 'newmaxscore' in form:
        try:
            newmaxscore = float(form['newmaxscore'])
        except (ValueError, TypeError):
            newmaxscore = None
        DB.update_qt_maxscore(qt_id, newmaxscore)

    newname = False
    if 'newattachmentname' in form:
        if len(form['newattachmentname']) > 1:
            newname = form['newattachmentname']
    if 'newattachment' in request.files:
        fptr = request.files['newattachment']
        if not newname:
            # If they haven't supplied a filename we use
            # the name of the file they uploaded.
            # TODO: Security check? We don't create disk files with this name
            newname = fptr.filename
        data = fptr.read()
        mtype = fptr.content_type
        DB.create_qt_att(qt_id, newname, mtype, data, version)
        log(INFO, "File '%s' uploaded by %s" % (newname, session['username']))

    flash("Question changes saved")
    return redirect(url_for("qedit_raw_edit", topic_id=topic_id, qt_id=qt_id))


@app.route("/qedit_raw/att/<int:qt_id>/<fname>")
@authenticated
def qedit_raw_attach(qt_id, fname):
    """ Serve the given question template attachment
        straight from DB so it's fresh
    """
    mtype = DB.get_qt_att_mimetype(qt_id, fname)
    data = DB.get_qt_att(qt_id, fname)
    if not data:
        abort(404)
    if not mtype:
        mtype = "text/plain"
    if mtype == "text/html":
        mtype = "text/plain"
    sio = StringIO.StringIO(data)
    return send_file(sio, mtype, as_attachment=True, attachment_filename=fname)


@app.route("/qedit_oqe/edit/<int:topic_id>/<int:qt_id>")
@authenticated
def qedit_oqe_edit(topic_id, qt_id):
    """ Present a question editor so they can edit the question template.
        Main page of editor
    """
    user_id = session['user_id']

    course_id = Topics.get_course_id(topic_id)

    if not (check_perm(user_id, course_id, "courseadmin")
            or check_perm(user_id, course_id, "courseadmin")
            or check_perm(user_id, course_id, "questionedit")
            or check_perm(user_id, course_id, "questionsource")):
        flash("You do not have question editor privilege in this course")
        return redirect(url_for("cadmin_edit_topic",
                                course_id=course_id, topic_id=topic_id))

    course = Courses2.get_course(course_id)
    topic = Topics.get_topic(topic_id)
    qtemplate = DB.get_qtemplate(qt_id)
    try:
        html = DB.get_qt_att(qt_id, "qtemplate.html")
    except KeyError:
        try:
            html = DB.get_qt_att(qt_id, "__qtemplate.html")
        except KeyError:
            html = "[question html goes here]"

    qtemplate['html'] = html
    attachnames = DB.get_qt_atts(qt_id, version=qtemplate['version'])
    attachments = [
        {
            'name': name,
            'mimetype': DB.get_qt_att_mimetype(qt_id, name)
        } for name in attachnames
        if name not in ['qtemplate.html', 'image.gif', 'datfile.txt',
                        '__datfile.txt', '__qtemplate.html']
    ]

    return render_template(
        "courseadmin_oqe_edit.html",
        course=course,
        topic=topic,
        html=html,
        attachments=attachments,
        attachnames=attachnames,
        qtemplate=qtemplate
    )
