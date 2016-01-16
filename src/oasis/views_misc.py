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
from logging import getLogger

from .lib import Users2, DB, Topics, \
    Courses2, Attach, QEditor, QEditor2

MYPATH = os.path.dirname(__file__)

from .lib.Audit import audit
from .lib.Permissions import check_perm

from oasis import app, authenticated

L = getLogger("oasisqe")


# Does its own auth because it may be used in embedded questions
@app.route("/att/qatt/<int:qt_id>/<int:version>/<int:variation>/<fname>")
def attachment_question(qt_id, version, variation, fname):
    """ Serve the given question attachment. This will come specifically from the question, not the qtemplate.
        :param qt_id: ID of the QTemplate
        :param version: QTemplate version
        :param variation: Which variation of the QTemplate
        :param fname: The "filename" of the attachment
    """
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
    """ Serve the given question template attachment.
        :param qt_id: ID of the QTemplate
        :param version: QTemplate version
        :param variation: Which variation of the QTemplate
        :param fname: The "filename" of the attachment
    """
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
    """ Give them a custom 401 error.
        :param error: A string containing the message.
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
    """ Work out the appropriate question editor and redirect to it
        :param course_id: ID of the course the question is in.
        :param topic_id: ID of the topic the question is in.
        :param qt_id: ID of the question template.
    """
    etype = DB.get_qt_editor(qt_id)
    if etype == "Raw":
        return redirect(url_for("qedit_raw_edit",
                                topic_id=topic_id,
                                qt_id=qt_id))
    if etype == "qe2":
        return redirect(url_for("qedit_qe2_edit",
                                topic_id=topic_id,
                                qt_id=qt_id))

    flash("Unknown Question Type, can't Edit")
    return redirect(url_for('cadmin_edit_topic',
                            course_id=course_id,
                            topic_id=topic_id))


@app.route("/qedit_raw/qtlog/<int:topic_id>/<int:qt_id>")
@authenticated
def qedit_qtlog(topic_id, qt_id):
    """ Show a table of all recent error messages affecting that question.
        :param topic_id: ID of the topic the question is in
        :param qt_id: ID of the question template to display the log of.
    """

    errors = QEditor.qtlog_as_html(topic_id, qt_id)
    course_id = Topics.get_course_id(topic_id)
    course = Courses2.get_course(course_id)

    return render_template("qtlog_errors.html",
                           course=course,
                           topic_id=topic_id,
                           html=errors)


@app.route("/qedit_raw/edit/<int:topic_id>/<int:qt_id>")
@authenticated
def qedit_raw_edit(topic_id, qt_id):
    """ Present a question editor so they can edit the question template.
        Main page of editor
        :param topic_id: ID of the topic the question template is in.
        :param qt_id: ID of the Question Template to edit.
    """
    user_id = session['user_id']

    course_id = Topics.get_course_id(topic_id)

    if not (check_perm(user_id, course_id, "courseadmin") or
            check_perm(user_id, course_id, "courseadmin") or
            check_perm(user_id, course_id, "questionedit") or
            check_perm(user_id, course_id, "questionsource")):
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
    """ Accept the question editor form and save the results.
        :param topic_id: ID of the topic the question template is in.
        :param qt_id: ID of the Question Template to save.
    """
    valid = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    user_id = session['user_id']
    course_id = Topics.get_course_id(topic_id)
    if not (check_perm(user_id, course_id, "courseadmin") or
            check_perm(user_id, course_id, "courseadmin") or
            check_perm(user_id, course_id, "questionedit") or
            check_perm(user_id, course_id, "questionsource")):
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

    # Let the question editor deal with the rest
    QEditor.process_save(qt_id, topic_id, request, session, version)

    flash("Question changes saved")
    return redirect(url_for("qedit_raw_edit", topic_id=topic_id, qt_id=qt_id))


@app.route("/qedit_raw/att/<int:qt_id>/<fname>")
@authenticated
def qedit_raw_attach(qt_id, fname):
    """ Serve the given question template attachment
        straight from DB so it's fresh
        :param qt_id: ID of the Question Template the attachment belongs to.
        :param fname: The "filename" of the attachment.
    """
    mimetype = DB.get_qt_att_mimetype(qt_id, fname)
    data = DB.get_qt_att(qt_id, fname)
    if not data:
        abort(404)
    if not mimetype:
        mimetype = "text/plain"
    if mimetype == "text/html":
        mimetype = "text/plain"
    sio = StringIO.StringIO(data)
    return send_file(sio, mimetype, as_attachment=True, attachment_filename=fname)


@app.route("/qedit_qe2/edit/<int:topic_id>/<int:qt_id>")
@authenticated
def qedit_qe2_edit(topic_id, qt_id):
    """ Present a question editor so they can edit the question template.
        Main page of editor. This is the "QE2" editor. Currently not functional.
        :param topic_id: ID of the topic the question template is in.
        :param qt_id: ID of the Question Template to edit.
    """
    user_id = session['user_id']

    course_id = Topics.get_course_id(topic_id)

    if not (check_perm(user_id, course_id, "courseadmin") or
            check_perm(user_id, course_id, "courseadmin") or
            check_perm(user_id, course_id, "questionedit") or
            check_perm(user_id, course_id, "questionsource")):
        flash("You do not have question editor privilege in this course")
        return redirect(url_for("cadmin_edit_topic",
                                course_id=course_id, topic_id=topic_id))

    course = Courses2.get_course(course_id)
    topic = Topics.get_topic(topic_id)
    qtemplate = DB.get_qtemplate(qt_id)
    try:
        html = DB.get_qt_att(qt_id, "_editor.qe2")
    except KeyError:
        html = "[ERROR: Missing question editor data]"

    qtemplate['html'] = html
    attachnames = DB.get_qt_atts(qt_id, version=qtemplate['version'])
    attachments = [
        {
            'name': name,
            'mimetype': DB.get_qt_att_mimetype(qt_id, name)
        } for name in attachnames
        if not name.startswith("_")
        ]

    return render_template(
            "courseadmin_qe2_edit.html",
            course=course,
            topic=topic,
            html=html,
            attachments=attachments,
            attachnames=attachnames,
            qtemplate=qtemplate
    )

@app.route("/qedit_qe2/save/<int:topic_id>/<int:qt_id>", methods=['POST', ])
@authenticated
def qedit_qe2_save(topic_id, qt_id):
    """ Accept the question editor form and save the results.
        :param topic_id: ID of the topic the question template is in.
        :param qt_id: ID of the Question Template to save.
    """
    valid_embed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    user_id = session['user_id']
    course_id = Topics.get_course_id(topic_id)
    if not (check_perm(user_id, course_id, "courseadmin") or
            check_perm(user_id, course_id, "courseadmin") or
            check_perm(user_id, course_id, "questionedit") or
            check_perm(user_id, course_id, "questionsource")):
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
                            if ch in valid_embed])
        if not DB.update_qt_embedid(qt_id, embed_id):
            flash("Error updating EmbedID, "
                  "possibly the value is already used elsewhere.")

    # Let the question editor deal with the rest
    try:
        QEditor2.process_save(qt_id, topic_id, request, session, version)
    except KeyError, e:
        abort(400)

    flash("Question changes saved")
    return redirect(url_for("qedit_qe2_edit", topic_id=topic_id, qt_id=qt_id))
