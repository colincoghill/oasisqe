# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Practice related backend code
"""

import re
from logging import log, WARN
from oasis.lib import OaGeneral

from oasis.lib.OaUserDB import checkPerm
from oasis.lib.OaExceptions import OaMarkerError
from . import OaConfig, OaDB, OaPool, Topics

fileCache = OaPool.fileCache(OaConfig.cachedir)


def getPracticeQuestion(qtid, user_id):
    """ Find an existing, or create a new, practice question
        for the given user."""
    try:
        qtid = int(qtid)
        assert qtid > 0
    except (ValueError, TypeError, AssertionError):
        log(WARN, "Called with bad qtid %s?" % qtid)
    qid = OaDB.getQuestionByQTStudent(qtid, user_id)
    if not qid is False:
        return int(qid)
    qid = OaGeneral.generateQuestion(qtid, user_id)
    try:
        qid = int(qid)
    except (ValueError, TypeError):
        log(WARN,
            "generateQuestion(%s,%s) Fail: returned %s" % (qtid, user_id, qid))
    else:
        OaDB.setQuestionViewTime(qid)
    return qid


def getSortedQuestionList(course, topic, user_id=None):
    def cmp_question_position(a, b):
        """Order questions by the absolute value of their positions
           since we use -'ve to indicate hidden.
        """
        return cmp(abs(a['position']), abs(b['position']))

    questionlist = OaGeneral.getQuestionListing(topic, user_id, numdone=False)
    if questionlist:
        # Filter out the questions without a positive position unless
        # the user has prevew permission.
        canpreview = checkPerm(user_id, course, "OASIS_PREVIEWQUESTIONS")
        if not canpreview:
            questionlist = [question for question in questionlist
                            if question['position'] > 0]
        else:
            # At the moment we use -'ve positions to indicate that a question
            # is hidden but when displaying them we want to maintain the sort
            # order.
            for question in questionlist:
                # Usually questions with position 0 are broken or
                # uninteresting so put them at the bottom.
                if question['position'] == 0:
                    question['position'] = -10000
            questionlist.sort(cmp_question_position)
    else:
        questionlist = []
    return questionlist


def getSortedQuestionListWithStats(course, topic, user_id=None):
    def cmp_question_position(a, b):
        """Order questions by the absolute value of their positions
           since we use -'ve to indicate hidden.
        """
        return cmp(abs(a['position']), abs(b['position']))

    questionlist = OaGeneral.getQuestionListing(topic, user_id, numdone=False)
    if not questionlist:
        return []
        # Filter out the questions without a positive position unless
    # the user has prevew permission.
    questions = [question for question in questionlist
                 if question['position'] > 0]
    questions.sort(cmp_question_position)
    for question in questions:
        question['maxscore'] = OaDB.getQTemplateMaxScore(question['qtid'])

        stats_1 = OaDB.getStudentQuestionPracticeStats(user_id, question['qtid'], 3)
        if stats_1: # Last practices
            # Date of last practice
            question['age'] = stats_1[(len(stats_1) - 1)]['age']
            question['ageseconds'] = stats_1[(len(stats_1) - 1)]['ageseconds']
            # Fetch last three scores and rate them as good, average or poor
            for attempt in stats_1:
                if question['maxscore'] > 0:
                    attempt['pscore'] = "%d%%" % ((attempt['score'] / question['maxscore']) * 100,)
                    attempt['rating'] = 2  # average
                    if attempt['score'] == question['maxscore']:
                        attempt['rating'] = 3  # good
                    if attempt['score'] == 0:
                        attempt['rating'] = 1  # poor

                else:  # don't have maxscore so don't make score a percentage
                    attempt['pscore'] = "%2.1f " % (attempt['score'],)
                    if attempt['score'] == 0:
                        attempt['rating'] = 1
            question['stats'] = stats_1
        else:
            question['stats'] = None
        stats_2 = OaDB.fetchQuestionStatsInClass(course, question['qtid'])
        if not stats_2:  # no stats, make some up
            stats_2 = {'num': 0, 'max': 0, 'min': 0, 'avg': 0}
            percentage = 0
        else:
            if stats_2['max'] == 0:
                percentage = 0
            else:
                percentage = int(stats_2['avg'] / stats_2['max'] * 100)
        question['classpercent'] = str(percentage) + "%"
        individualstats = OaDB.getIndividualPracticeStats(user_id, question['qtid'])
        if not individualstats:
            indivpercentage = 0
        else:
            if stats_2['max'] == 0:
                indivpercentage = 0
            else:
                indivpercentage = int(individualstats['avg'] / stats_2['max'] * 100)
        question['indivpercent'] = str(indivpercentage) + "%"
    return questions


def isQuestionBlockedToUser(user_id, c_id, topic_id, qt_id):
    """ Is the user blocked from seeing the practice question?
        False if they can view it
        True, or a (str) error message indicating why it's blocked.
    """
    topicvisibility = Topics.getVisibility(topic_id)
    canpreview = checkPerm(user_id, c_id, "OASIS_PREVIEWQUESTIONS")
    # They're trying to go directly to a hidden question?
    position = OaDB.getQTemplatePositionInTopic(qt_id, topic_id)
    if position <= 0 and not canpreview:
        return "Access denied to question."
        # They're trying to go directly to a question in an invisible category?
    if topicvisibility <= 1 and not canpreview:
        return "Access denied to question."
    return False


def getNextPrev(qt_id, topic_id):
    """ Find the "next" and "previous" qtemplates, by topic, position. """
    if not topic_id:
        return None, None
        # This is very inefficient, but with the way questions are stored,
        # I didn't see a better way. Could maybe be revisited some time?
    questionlist = OaGeneral.getQuestionListing(topic_id, numdone=False)
    if questionlist:
        # Filter out the questions without a positive position
        questionlist = [question
                        for question in questionlist
                        if question['position'] > 0]
    else:
        questionlist = []
        # We need to step through the list finding the "next and previous" id's
    nextid = None
    foundprev = None
    previd = None
    foundcurrent = None
    for i in questionlist:
        if foundcurrent:
            nextid = int(i['qtid'])
            break
        if int(i['qtid']) == int(qt_id):
            foundprev = True
            foundcurrent = True
        if not foundprev:
            previd = int(i['qtid'])
        # previd and nextid should now contain the correct values
    # or None, if they are not valid (current_qtid is the first or
    # last question)
    return previd, nextid


def markQuestion(user_id, topic_id, q_id, request):
    """Mark the question and return the results"""
    answers = {}
    for i in request.form.keys():
        part = re.search(r"^Q_(\d+)_ANS_(\d+)$", i)
        if part:
            newqid = int(part.groups()[0])
            part = int(part.groups()[1])
            if newqid == q_id:
                value = request.form[i]
                answers["G%d" % part] = value
                OaDB.saveGuess(newqid, part, value)
            else:
                log(WARN,
                    "received guess for wrong question? (%d,%d,%d,%s)" % (user_id, topic_id, q_id, request.form))
    try:
        marks = OaGeneral.markQuestion(q_id, answers)
        OaDB.setQuestionStatus(q_id, 3)    # 3 = marked
        OaDB.setQuestionMarkTime(q_id)
    except OaMarkerError:
        log(WARN, "Marker Error - (%d, %d, %d, %s)" % (user_id, topic_id, q_id, request.form))
        marks = {}
    q_body = OaGeneral.renderMarkResults(q_id, marks)
    parts = [int(var[1:]) for var in marks.keys() if re.search("^A([0-9]+)$", var) > 0]
    parts.sort()
    total = 0.0
    for part in parts:
        if marks.has_key('M%d' % (part,)):
            total += float(marks['M%d' % (part,)])
    OaDB.updateQuestionScore(q_id, total)    # 3 = marked
    OaDB.setQuestionStatus(q_id, 2)
    return q_body
