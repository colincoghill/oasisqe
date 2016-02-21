# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Practice related backend code
"""

import re
from oasis.lib import General

from oasis.lib.Permissions import check_perm
from oasis.lib.OaExceptions import OaMarkerError
from . import DB, Topics
from logging import getLogger

L = getLogger("oasisqe")


def get_practice_q(qt_id, user_id):
    """ Find an existing, or create a new, practice question
        for the given user."""
    try:
        qt_id = int(qt_id)
        assert qt_id > 0
    except (ValueError, TypeError, AssertionError):
        L.warn("Called with bad qtid %s?" % qt_id)
    qid = DB.get_q_by_qt_student(qt_id, user_id)
    if qid is not False:
        return int(qid)
    qid = General.gen_q(qt_id, user_id)
    try:
        qid = int(qid)
    except (ValueError, TypeError):
        L.warn("generateQuestion(%s,%s) Fail: returned %s" % (qt_id, user_id, qid))
    else:
        DB.set_q_viewtime(qid)
    return qid


def get_sorted_questions(course_id, topic_id, user_id=None):
    """ Return a list of questions, sorted by position
    """

    def cmp_question_position(a, b):
        """Order questions by the absolute value of their positions
           since we use -'ve to indicate hidden.
        """
        return cmp(abs(a['position']), abs(b['position']))

    questionlist = General.get_q_list(topic_id, user_id, numdone=False)
    if questionlist:
        # Filter out the questions without a positive position unless
        # the user has prevew permission.
        canpreview = check_perm(user_id, course_id, "questionpreview")
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


def get_sorted_qlist_wstats(course_id, topic_id, user_id=None):
    """ Return a list of questions, sorted by position. With
        some statistics (may be expensive to calculate).
    """
    def cmp_question_position(a, b):
        """Order questions by the absolute value of their positions
           since we use -'ve to indicate hidden.
        """
        return cmp(abs(a['position']), abs(b['position']))

    questionlist = General.get_q_list(topic_id, user_id, numdone=False)
    if not questionlist:
        return []
        # Filter out the questions without a positive position unless
    # the user has prevew permission.
    questions = [question for question in questionlist
                 if question['position'] > 0]
    questions.sort(cmp_question_position)
    for question in questions:
        try:
            question['maxscore'] = DB.get_qt_maxscore(question['qtid'])
        except KeyError:
            question['maxscore'] = 0

        stats_1 = DB.get_student_q_practice_stats(user_id, question['qtid'], 3)
        if stats_1:  # Last practices
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
        stats_2 = DB.get_q_stats_class(course_id, question['qtid'])
        if not stats_2:  # no stats, make some up
            stats_2 = {'num': 0, 'max': 0, 'min': 0, 'avg': 0}
            percentage = 0
        else:
            if stats_2['max'] == 0:
                percentage = 0
            else:
                percentage = int(stats_2['avg'] / stats_2['max'] * 100)
        question['classpercent'] = str(percentage) + "%"
        user_stats = DB.get_prac_stats_user_qt(user_id, question['qtid'])
        if not user_stats:
            indivpercentage = 0
        else:
            if stats_2['max'] == 0:
                indivpercentage = 0
            else:
                indivpercentage = int(user_stats['avg'] / stats_2['max'] * 100)
        question['indivpercent'] = str(indivpercentage) + "%"
    return questions


def is_q_blocked(user_id, course_id, topic_id, qt_id):
    """ Is the user blocked from seeing the practice question?
        False if they can view it
        True, or a (str) error message indicating why it's blocked.
    """
    topicvisibility = Topics.get_vis(topic_id)
    canpreview = check_perm(user_id, course_id, "questionpreview")
    # They're trying to go directly to a hidden question?
    position = DB.get_qtemplate_practice_pos(qt_id)
    if position <= 0 and not canpreview:
        return "Access denied to question."
        # They're trying to go directly to a question in an invisible category?
    if topicvisibility <= 1 and not canpreview:
        return "Access denied to question."
    return False


def get_next_prev_pos(qt_id, topic_id):
    """ Find the positions of the "next" and "previous" qtemplates in the practice topic..
        Returns their positions."""

    if not topic_id:
        return None, None
        # This is very inefficient, but with the way questions are stored,
        # I didn't see a better way. Could maybe be revisited some time?

    pos = DB.get_qtemplate_practice_pos(qt_id)
    if not pos:
        return None, None

    maxp = DB.get_qt_max_pos_in_topic(topic_id)
    if pos == maxp:
        next_pos = None
    else:
        p = pos + 1
        while p < maxp and not DB.get_qtemplates_in_topic_position(topic_id, p):
            p += 1
        next_pos = p

    p = pos - 1
    while p > 0 and not DB.get_qtemplates_in_topic_position(topic_id, p):
        p -= 1
    if p == 0:
        prev_pos = None
    else:
        prev_pos = p

    return prev_pos, next_pos


def mark_q(user_id, topic_id, q_id, request):
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
                DB.save_guess(newqid, part, value)
            else:
                L.warn("received guess for wrong question? (%d,%d,%d,%s)" %
                    (user_id, topic_id, q_id, request.form))
    try:
        marks = General.mark_q(q_id, answers)
        DB.set_q_status(q_id, 3)    # 3 = marked
        DB.set_q_marktime(q_id)
    except OaMarkerError:
        L.warn("Marker Error - (%d, %d, %d, %s)" %
            (user_id, topic_id, q_id, request.form))
        marks = {}
    q_body = General.render_mark_results(q_id, marks)
    parts = [int(var[1:])
             for var in marks.keys()
             if re.search(r"^A([0-9]+)$", var) > 0]
    parts.sort()
    total = 0.0
    for part in parts:
        if 'M%d' % (part,) in marks:
            total += float(marks['M%d' % (part,)])
    DB.update_q_score(q_id, total)    # 3 = marked
    DB.set_q_status(q_id, 2)
    return q_body
