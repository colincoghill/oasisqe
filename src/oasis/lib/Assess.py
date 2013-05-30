# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Assessment related functionality.
"""

import re

from oasis.lib.OaExceptions import OaMarkerError
from logging import log, INFO, ERROR, WARN
from oasis.lib import DB, General, Exams, Courses


DATEFORMAT = "%d %b %H:%M"


def mark_exam(user_id, exam_id):
    """ Submit the assessment and mark it.
        Returns True if it went well, or False if a problem.
    """
    numQuestions = Exams.getNumQuestions(exam_id)
    status = Exams.getUserStatus(user_id, exam_id)
    log(INFO, "Marking assessment %s for %s, status is %s" % (exam_id, user_id, status))
    examtotal = 0.0
    for position in range(1, numQuestions + 1):
        q_id = General.getExamQuestion(exam_id, position, user_id)
        answers = DB.get_q_guesses(q_id)
        # There's a small chance they got here without ever seeing a question, make sure it exists.
        DB.add_exam_q(user_id, exam_id, q_id, position)

        # First, mark the question
        try:
            marks = General.markQuestion(q_id, answers)
            DB.set_q_status(q_id, 3)    # 3 = marked
            DB.set_q_marktime(q_id)
        except OaMarkerError:
            log(WARN, "Marker Error in question %s, exam %s, student %s!" % (q_id, exam_id, user_id))
            return False
        parts = [int(var[1:]) for var in marks.keys() if re.search("^A([0-9]+)$", var) > 0]
        parts.sort()

        # Then calculate the mark
        total = 0.0
        for part in parts:
            try:
                mark = float(marks['M%d' % (part,)])
            except (KeyError, ValueError):
                mark = 0
            total += mark
            DB.update_q_score(q_id, total)
        examtotal += total

    Exams.setUserStatus(user_id, exam_id, 5)
    Exams.setSubmitTime(user_id, exam_id)
    Exams.saveScore(exam_id, user_id, examtotal)
    Exams.touchUserExam(exam_id, user_id)

    log(INFO, "user %s scored %s total on exam %s" % (user_id, examtotal, exam_id))
    return True


def student_exam_duration(student, exam_id):
    """ How long did the assessment take.
        returns   starttime, endtime
        either could be None if it hasn't been started/finished
    """

    firstview = None

    examsubmit = Exams.getSubmitTime(exam_id, student)
    questions = General.getExamQuestions(student, exam_id)

    # we're working out the first time the assessment was viewed is the
    # earliest time a question in it was viewed
    # It's possible (although unlikely) that they viewed a question other than the first page, first.
    for question in questions:
        questionview = DB.get_q_viewtime(question)
        if firstview:
            if questionview < firstview:
                firstview = questionview
        else:
            firstview = questionview
    return firstview, examsubmit


def render_own_marked_exam(student, exam):
    """ Return a students instance of the exam, with HTML version of the question,
        their answers, and a marking summary.

        returns list of questions/marks
        [  {'pos': position,
            'html': rendered (marked) question,
            'marking': [ 'part': part number,
                         'guess':   student guess,
                         'correct': correct answer,
                         'mark':    (float) mark,
                         'tolerance':  marking tolerance,
                         'comment':   marking comment
                         ]
           }, ...
        ]
    """
    questions = General.getExamQuestions(student, exam)
    firstview, examsubmit = student_exam_duration(student, exam)
    results = []

    examtotal = 0.0
    for question in questions:
        qtemplate = DB.get_q_parent(question)

        answers = DB.get_q_guesses_before_time(question, examsubmit)
        pos = DB.get_qt_exam_pos(exam, qtemplate)
        marks = General.markQuestion(question, answers)
        parts = [int(var[1:]) for var in marks.keys() if re.search("^A([0-9]+$)", var) > 0]
        parts.sort()
        marking = []
        for part in parts:
            guess = marks['G%d' % (part,)]

            if guess == "None":
                guess = None
            answer = marks['A%d' % (part,)]
            score = marks['M%d' % (part,)]
            tolerance = marks['T%d' % (part,)]
            comment = marks['C%d' % (part,)]
            examtotal += score
            marking.append({
                'part': part,
                'guess': guess,
                'correct': answer,
                'mark': score,
                'tolerance': tolerance,
                'comment': comment
            })

        html = General.render_q_html(question)
        results.append({
            'pos': pos,
            'html': html,
            'marking': marking
        })
    return results, examtotal


def get_exam_list_sorted(user_id, previous_years=False):
    """ Return a list of exams for the given user. """
    courses = Courses.getAll()
    exams = []
    for cid in courses:
        try:
            exams += [Exams.getExamStruct(e, user_id) for e in Courses.get_exams(cid, previous_years=previous_years)]
        except KeyError, err:
            log(ERROR, "Failed fetching exam list for user %s: %s" % (user_id, err))
    exams.sort(key=lambda y: y['start_epoch'], reverse=True)
    return exams
