# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" OaEmbed.py

    Allow us to embed OASIS questions into pages from other places,
    eg. web tutorials.

    http://host:port/oasis/embed/question/QTID/question.html, will POST to:
    http://host:port/oasis/embed/question/QTID/mark.html,

    Marked page may contain link to Try Again

"""

import re

from logging import log, INFO
from oasis.lib.OaExceptions import OaMarkerError
from oasis.lib import DB, General


def mark_q(user_id, qtid, request):
    """Mark the question and show a page containing marking results."""

    if "OaQID" in request.form:
        qid = int(request.form["OaQID"])
    else:
        qid = None

    out = u""
    answers = {}
    for i in request.form.keys():
        part = re.search(r"^Q_(\d+)_ANS_(\d+)$", i)
        if part:
            newqid = int(part.groups()[0])
            part = int(part.groups()[1])

            value = request.form[i]
            answers["G%d" % part] = value
            DB.save_guess(newqid, part, value)

    if qid:
        try:
            marks = General.mark_q(qid, answers)
            DB.set_q_status(qid, 3)    # 3 = marked
            DB.set_q_marktime(qid)
        except OaMarkerError:
            log(INFO,
                "getMarkQuestionPage(%d, %d, %s) Marker ERROR" %
                (user_id, qtid, request.form))
            marks = {}

        out += General.render_mark_results(qid, marks)
        parts = [int(var[1:])
                 for var in marks.keys()
                 if re.search("^A([0-9]+)$", var) > 0]
        parts.sort()
        total = 0.0
        for part in parts:
            if marks.has_key('M%d' % (part,)):
                total += float(marks['M%d' % (part,)])

    return out



