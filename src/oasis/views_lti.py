# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Views for LTI related requests.
    Using LTI, other elearning applications can embed OASIS practice questions and assessments.

    We use the PyLTI library from  https://github.com/mitodl/pylti

    We take the email address given by the LTI consumer and associate the request with a local
    account with the same email.  If one is not found, we create a local account with that
    email address and default access and use that. 

    Implemented:

       Launching a practice question
       Launching an assessment

    Not Implemented:
       Returning the results
"""

import os
from flask import render_template,redirect,url_for, abort,session
from pylti.flask import lti

MYPATH = os.path.dirname(__file__)

from oasis import app,csrf,audit
from logging import getLogger
from .lib import Users2, LTIConsumers, OaConfig

L = getLogger("oasisqe")

LTIConsumers.update_lti_config()


def error(exception=None):
    """ render error page
    :param exception: optional exception
    :return: the error.html template rendered
    """

    return render_template('lti_error.html',
                           exception=exception)


def _auth_user(lti, app):
    """ Given an lti object, find or create the local user account, then set up the session."""

    global session

    lti_consumer = LTIConsumers.LTIConsumer(consumer_key=lti.key)
    username_attribute = lti_consumer.username_attribute

    try:
        username = getattr(lti, u"%s"%username_attribute)
        if not username:
            abort(400, "'%s' field was empty" % username_attribute)

    except AttributeError:
        L.error("Unable to lookup lti attribute '%s' for username mapping" % username_attribute)
        abort(400, "Expecting '%s' in LTI params" % username_attribute)

    user_id = Users2.uid_by_uname(username)
    if not user_id:
        audit(1, user_id, user_id, "UserAuth",
              "Created user %s because of LTI request for unknown user" % username)
        L.info("creating OASIS user %s for LTI (%s: %s) " % (username, lti.key, lti_consumer.title))
        # uname, passwd, givenname, familyname, acctstatus, studentid, email = None
        Users2.create(username, 'lti-nologin-direct', '', '', 1, '', username, None, 'lti', '', True)
        user_id = Users2.uid_by_uname(username)

    if not user_id:
        abort(400, "Unable to Authenticate")

    user = Users2.get_user(user_id)
    session['username'] = username
    session['user_id'] = user_id
    session['user_givenname'] = user['givenname']
    session['user_familyname'] = user['familyname']
    session['user_fullname'] = user['fullname']
    session['user_display_name'] = user['display_name']

    session['user_authtype'] = "ltiauth"

    audit(1, user_id, user_id, "UserAuth",
          "%s successfully logged in via ltiauth" % session['username'])

    return session


@app.route("/lti", methods=["POST", "GET"])
@lti(request='any', error=error, app=app)
@csrf.exempt
def lti_launch(lti):
    """
    Just testing at the moment
    :return:
    """
    _session = _auth_user(lti, app)

    return render_template(
        "lti_launch.html",
        lti=lti,
        session=_session)


@app.route("/lti/main", methods=["POST", "GET"])
@lti(request='any', error=error, app=app)
@csrf.exempt
def lti_main(lti):
    """
    Authenticate the user and send them to Top Menu
    :return:
    """
    _auth_user(lti, app)

    return redirect(url_for("main_top"))


@app.route("/lti/practice", methods=["POST", "GET"])
@lti(request='any', error=error, app=app)
@csrf.exempt
def lti_practice(lti):
    """
    Authenticate the user and send them to Practice
    :return:
    """
    _auth_user(lti, app)
    return redirect(url_for("practice_top"))


@app.route("/lti/practice/subcategory/<int:topic_id>", methods=["POST", "GET"])
@lti(request='any', error=error, app=app, topic_id=False)
@csrf.exempt
def lti_practice_topic(topic_id, lti=lti):
    """
    Authenticate the user and send them to Practice Topic
    :return:
    """
    _auth_user(lti, app)
    return redirect(url_for("practice_choose_question", topic_id=topic_id))


@app.route("/lti/assess", methods=["POST", "GET"])
@lti(request='any', error=error, app=app)
@csrf.exempt
def lti_assess(lti):
    """
    Authenticate the user and send them to Assessments
    :return:
    """
    _auth_user(lti, app)
    return redirect(url_for("assess_top"))


@app.route("/lti/assess/startexam/<int:course_id>/<int:exam_id>", methods=["POST", "GET"])
@lti(request='any', error=error, app=app, topic_id=False)
@csrf.exempt
def lti_assess_startexam(course_id, exam_id, lti=lti):
    """
    Authenticate the user and send them to the Assessment
    :return:
    """
    _auth_user(lti, app)
    return redirect(url_for("assess_startexam", course_id=course_id, exam_id=exam_id))


