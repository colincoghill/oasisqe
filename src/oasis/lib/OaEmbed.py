# -*- coding: utf-8 -*-

""" OaEmbed.py

    Allow us to embed OASIS questions into pages from other places, eg. web tutorials.

    http://host:port/oasis/embed/question/QTID/question.html, will POST to:
    http://host:port/oasis/embed/question/QTID/mark.html, which will allow    Try Again

"""

import re

from logging import log, INFO
from oasis.lib.OaExceptions import OaMarkerError
from oasis.lib import OaDB, OaGeneral


def markQuestion(user_id, qtid, request):
    """Mark the question and show a page containing marking results."""

    if "OaQID" in request.form:
        qid = int(request.form["OaQID"])
    else:
        qid = None

    out = u""
    answers = {}
    for i in request.form.keys():
        part = re.search("^Q_(\d+)_ANS_(\d+)$", i)
        if part:
            newqid = int(part.groups()[0])
            part = int(part.groups()[1])

            value = request.form[i]
            answers["G%d" % part] = value
            OaDB.saveGuess(newqid, part, value)

    if qid:
        try:
            marks = OaGeneral.markQuestion(qid, answers)
            OaDB.setQuestionStatus(qid, 3)    # 3 = marked
            OaDB.setQuestionMarkTime(qid)
        except OaMarkerError:
            log(INFO, "OaEmbed:getMarkQuestionPage(%d, %d, %s) Marker ERROR" % (user_id, qtid, request.form))
            marks = {}

        out += OaGeneral.renderMarkResults(qid, marks)
        parts = [int(var[1:]) for var in marks.keys() if re.search("^A([0-9]+)$", var) > 0]
        parts.sort()
        total = 0.0
        for part in parts:
            if marks.has_key('M%d' % (part,)):
                total += float(marks['M%d' % (part,)])

    return out



