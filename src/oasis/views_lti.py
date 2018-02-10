# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Views for LTI related requests.
    Using LTI, other elearning applications can embed OASIS practice questions
"""

import os
from flask import render_template,abort
from pylti.flask import lti

MYPATH = os.path.dirname(__file__)

from oasis import app,csrf,audit
from logging import getLogger
from .lib import Users2, LTIConsumers

L = getLogger("oasisqe")




def error(exception=None):
    """ render error page
    :param exception: optional exception
    :return: the error.html template rendered
    """
    return render_template('lti_error.html',
                           exception=exception)


@app.route("/lti", methods=["POST", "GET"])
@lti(request='initial', error=error, app=app)
@csrf.exempt
def lti_launch(lti):
    """
    Just testing at the moment
    :return:
    """

    session = dict()

    username = lti.name
    user_id = Users2.uid_by_uname(username)
    if not user_id:
        if 'lis_person_name_given' in lti.lti_kwargs:
            given_name = lti.lis_person_name_given
        audit(1, user_id, user_id, "UserAuth",
              "Created user %s because of LTI request for unknown user" % username)
        Users2.create(username, 'lti-nologin-direct', '', '', 1, '', username, None, 'lti', '', True)
        user_id = Users2.uid_by_uname(username)

    user = Users2.get_user(user_id)
    session['username'] = username
    session['user_id'] = user_id
    session['user_givenname'] = user['givenname']
    session['user_familyname'] = user['familyname']
    session['user_fullname'] = user['fullname']
    session['user_authtype'] = "ltiauth"

    audit(1, user_id, user_id, "UserAuth",
          "%s successfully logged in via webauth" % session['username'])

    return render_template(
        "lti_launch.html",
        lti=lti,
        session=session)


LTIConsumers.update_lti_config()