# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html


import os
import StringIO

from flask import render_template, session, \
    request, redirect, abort, url_for, flash, \
    send_file, Response
from logging import log, INFO

from .lib import UserAPI, OaDB, Topics, \
    CourseAPI, OaAttachment, OaQEditor

MYPATH = os.path.dirname(__file__)

from .lib.Audit import audit
from .lib.OaUserDB import checkPermission

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
    attachments = [
        {
            'name': name,
            'mimetype': OaDB.getQTAttachmentMimeType(qt_id, name)
        } for name in attachnames if
        not name in ['qtemplate.html', 'image.gif', 'datfile.txt', '__datfile.txt', '__qtemplate.html']
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
