# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Views for question embedding.
"""

import os
from flask import render_template, session, request, abort
from .lib import Users2, DB, General, Practice, Embed

MYPATH = os.path.dirname(__file__)

from oasis import app

@app.route("/embed/question/<embed_id>/question.html")
# Does its own auth because it may be used in embedded questions
def embed_question(embed_id):
    """ Find an embed question and serve it.
        This should be suitable for including in an IFRAME or similar
    """

    VALIDCHARS=" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!.,?$@&"
    if 'user_id' not in session:
        user_id = Users2.getUidByUname("guest")
    else:
        user_id = session['user_id']

    if len(embed_id) < 1:
        abort(404)
    try:
        qtid = DB.get_qt_by_embedid(embed_id)
    except KeyError:
        qtid = None
        abort(404)

    title = request.args.get('title', DB.get_qt_name(qtid))
    title = ''.join([t for t in title
                     if t in VALIDCHARS])

    qid = Practice.get_practice_q(qtid, user_id)
    vers = DB.get_q_version(qid)
    if not vers >= DB.get_qt_version(qtid):
        qid = General.gen_q(qtid, user_id)

    q_body = General.render_q_html(qid)
    return render_template(
        "embeddoquestion.html",
        q_body=q_body,
        embed_id=DB.get_qt_embedid(qtid),
        title=title,
        qid=qid,
    )


@app.route("/embed/question/<embed_id>/mark.html", methods=["POST", "GET"])
# Does its own auth because it may be used in embedded questions
def embed_mark_question(embed_id):
    """ Find an embed question and serve it.
        This should be suitable for including in an IFRAME or similar
    """
    if 'user_id' not in session:
        user_id = Users2.getUidByUname("guest")
    else:
        user_id = session['user_id']

    qtid = DB.get_qt_by_embedid(embed_id)
    if not qtid:
        abort(404)

    if "OaQID" in request.form:
        qid = int(request.form["OaQID"])
    else:
        qid = None
    if not qid:
        abort(404)

    marking = Embed.mark_q(user_id, qtid, request)

    return render_template(
        "embedmarkquestion.html",
        embed_id=embed_id,
        marking=marking,
    )


@app.route("/embed/example.html")
# Does its own auth because it may be used in embedded questions
def embed_question_example():
    """ Give an example of embedding, as instructions."""
    return render_template("embedexample.html")
