# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Assessment related pages """

# Currently disabled until further testing has happened. Mostly complete and
# functional but it's really important this be right.

import os
import re
import time

from flask import render_template, session, \
    request, redirect, abort, url_for, flash

from .lib import OaDB, OaGeneral, Exams, CourseAPI, OaAssess

MYPATH = os.path.dirname(__file__)

from .lib.OaUserDB import check_perm

from oasis import app, authenticated


@app.route("/assess/top")
@authenticated
def assess_top():
    """ Top level assessment page. Let them choose an assessment."""
    user_id = session['user_id']
    exams = OaAssess.getSortedExamList(user_id=user_id, previous_years=False)
    current_num = len([e for e in exams if e['active']])
    upcoming_num = len([e for e in exams if e['future']])
    return render_template(
        "assesstop.html",
        exams=exams,
        current_num=current_num,
        upcoming_num=upcoming_num
    )


@app.route("/assess/previousexams")
@authenticated
def assess_previousexams():
    """ Show a list of older exams - from previous years """
    user_id = session['user_id']

    exams = OaAssess.getSortedExamList(user_id=user_id, previous_years=True)
    years = [e['start'].year for e in exams]
    years = list(set(years))
    years.sort(reverse=True)
    return render_template(
        "assesspreviousexams.html",
        exams=exams,
        years=years
    )


@app.route("/assess/assessmentunlock/<int:course_id>/<int:exam_id>",
           methods=['POST', ])
@authenticated
def assess_unlock(course_id, exam_id):
    """ An unlock code has been entered. """
    user_id = session['user_id']

    exam = Exams.getExamStruct(exam_id, user_id)

    if not check_perm(user_id, course_id, "OASIS_PREVIEWASSESSMENT"):
        if exam['future']:
            flash("That assessment is not yet available.")
            return redirect(url_for("assess_top"))

        if exam['past']:
            flash("That assessment is closed.")
            return redirect(url_for("assess_top"))

    if 'code' in request.form:
        ucode = request.form['code']
        session['code'] = ucode

        if exam['code'] == ucode:
            flash("Assessment unlocked.")
        else:
            flash("Incorrect unlock code.")

    return redirect(url_for("assess_startexam",
                            course_id=course_id,
                            exam_id=exam_id))


@app.route("/assess/startexam/<int:course_id>/<int:exam_id>")
@authenticated
def assess_startexam(course_id, exam_id):
    """ Show the start page of the exam """
    user_id = session['user_id']
    exam = Exams.getExamStruct(exam_id, user_id)

    if not check_perm(user_id, course_id, "OASIS_PREVIEWASSESSMENT"):
        if exam['future']:
            flash("That assessment is not yet available.")
            return redirect(url_for("assess_top"))

        if exam['past']:
            flash("That assessment is closed.")
            return redirect(url_for("assess_top"))

    Exams.createUserExam(user_id, exam_id)  # get it cached and ready to start

    if 'code' in session:
        ucode = session['code']
    else:
        ucode = ""

    if exam['code'] and exam['code'] != ucode:
        exam['locked'] = True
    else:
        exam['locked'] = False

    return render_template(
        "assessstart.html",
        course=CourseAPI.get_course(course_id),
        exam=exam
    )


@app.route("/assess/assessmentpage/<int:course_id>/<int:exam_id>/<int:page>",
           methods=['POST', 'GET'])
@authenticated
def assess_assessmentpage(course_id, exam_id, page):
    """ Display a page of the assessment and allow the user to fill in answers.
    """
    user_id = session['user_id']

    status = Exams.getUserStatus(user_id, exam_id)
    if status == 1:  # if it's not started, mark it as started
        Exams.setUserStatus(user_id, exam_id, 2)
        Exams.touchUserExam(exam_id, user_id)

    form = request.form
    for field in form.keys():
        qinfo = re.search(r"^Q_(\d+)_ANS_(\d+)$", field)
        if qinfo:
            q_id = int(qinfo.groups()[0])
            part = int(qinfo.groups()[1])
            value = form[field]
            timeremain = Exams.getEndTime(exam_id, user_id) - time.time()
            if timeremain < -30:
                flash("Time Exceeded, automatically submitting...")
                return redirect(url_for("assess_submit",
                                        course_id=course_id,
                                        exam_id=exam_id))

            if status < 6:
                OaDB.saveGuess(q_id, part, value)
        else:
            pass

    Exams.touchUserExam(exam_id, user_id)

    if "submit" in form:
        return redirect(url_for("assess_submit",
                                course_id=course_id,
                                exam_id=exam_id))

    if "goto" in form:
        goto = form['goto']

        if goto == "Finish":
            return redirect(url_for("assess_presubmit",
                                    course_id=course_id,
                                    exam_id=exam_id))

        if goto == "Start":
            return redirect(url_for("assess_startexam",
                                    course_id=course_id,
                                    exam_id=exam_id))

        page = int(goto.split(' ', 2)[1])

    q_id = OaGeneral.getExamQuestion(exam_id, page, user_id)
    timeleft = Exams.getEndTime(exam_id, user_id) - time.time()
    exam = Exams.getExamStruct(exam_id, course_id)

    if 'code' in session:
        ucode = session['code']
    else:
        ucode = ""

    if exam['code'] and exam['code'] != ucode:
        return redirect(url_for("assess_startexam",
                                course_id=course_id,
                                exam_id=exam_id))

    course = CourseAPI.get_course(course_id)
    if Exams.isDoneBy(user_id, exam_id):
        exam['is_done'] = True
        html = OaGeneral.render_q_html(q_id, readonly=True)
    else:
        html = OaGeneral.render_q_html(q_id)

    if exam['duration'] > 0:
        is_timed = 1
    else:
        is_timed = 0
    numquestions = Exams.getNumQuestions(exam_id)
    return render_template(
        "assess_page.html",
        exam=exam,
        course=course,
        course_id=course_id,
        page=page,
        pages=range(1, numquestions + 1),
        html=html,
        is_timed=is_timed,
        time_remain=timeleft,
        auto_submit=1
    )


@app.route("/assess/presubmit/<int:course_id>/<int:exam_id>")
@authenticated
def assess_presubmit(course_id, exam_id):
    """  Ask if they're sure they want to submit. """
    user_id = session['user_id']

    exam = Exams.getExamStruct(exam_id, course_id)
    course = CourseAPI.get_course(course_id)
    numquestions = Exams.getNumQuestions(exam_id)
    qids = []
    questions = []
    for position in range(1, numquestions + 1):
        q_id = OaDB.getExamQuestionByPositionStudent(exam_id, position, user_id)
        if q_id:
            qids.append(q_id)
            guesses = OaDB.getQuestionGuesses(q_id)
            keys = guesses.keys()
            keys.sort()
            questions.append({
                'guesses': [{'part': k[1:], 'guess': guesses[k]} for k in keys],
                'pos': position
            })

    return render_template(
        "assess_presubmit.html",
        exam=exam,
        course=course,
        course_id=course_id,
        qids=qids,
        questions=questions,
        page=1,
        pages=range(1, numquestions + 1)
    )


@app.route("/assess/submit/<int:course_id>/<int:exam_id>")
@authenticated
def assess_submit(course_id, exam_id):
    """  Submit and mark """
    user_id = session['user_id']

    exam = Exams.getExamStruct(exam_id, course_id)
    status = Exams.getUserStatus(user_id, exam_id)
    if status < 5:
        marked = OaAssess.markAssessment(user_id, exam_id)
        if not marked:
            flash("There was a problem marking the assessment, staff have been notified.")

    if exam["instant"] == 2:
        return redirect(url_for("assess_awaitresults",
                                course_id=course_id,
                                exam_id=exam_id))

    flash("Assessment has been marked.")
    return redirect(url_for("assess_viewmarked",
                            course_id=course_id,
                            exam_id=exam_id))


@app.route("/assess/awaitresults/<int:course_id>/<int:exam_id>")
@authenticated
def assess_awaitresults(course_id, exam_id):
    """  Thank them and tell them the results will be available later.
    """
    user_id = session['user_id']
    exam = Exams.getExamStruct(exam_id, course_id)
    course = CourseAPI.get_course(course_id)
    numquestions = Exams.getNumQuestions(exam_id)
    qids = []
    questions = []
    for position in range(1, numquestions + 1):
        q_id = OaDB.getExamQuestionByPositionStudent(exam_id, position, user_id)
        if q_id:
            qids.append(q_id)
            guesses = OaDB.getQuestionGuesses(q_id)
            keys = guesses.keys()
            keys.sort()
            questions.append({
                'guesses': [{'part': k[1:], 'guess': guesses[k]} for k in keys],
                'pos': position
            })
    return render_template(
        "assess_awaitresults.html",
        course=course,
        exam=exam,
        questions=questions,
        pages=range(1, numquestions + 1)
    )


@app.route("/assess/viewmarked/<int:course_id>/<int:exam_id>")
@authenticated
def assess_viewmarked(course_id, exam_id):
    """  Show them their marked assessment results """
    user_id = session['user_id']
    course = CourseAPI.get_course(course_id)
    try:
        exam = Exams.getExamStruct(exam_id, course_id)
    except KeyError:
        exam = {}
        abort(404)
    status = Exams.getUserStatus(user_id, exam_id)
    if not status >= 5:
        flash("Assessment is not marked yet.")
        return render_template(
            "assess_awaitresults.html",
            course=course,
            exam=exam
        )

    results, examtotal = OaAssess.renderOwnMarkedExam(user_id, exam_id)
    datemarked = OaGeneral.humanDate(Exams.getMarkTime(exam_id, user_id))
    datesubmit = OaGeneral.humanDate(Exams.getSubmitTime(exam_id, user_id))

    if "user_fullname" in session:
        fullname = session['user_fullname']
    else:
        fullname = ""
    if "username" in session:
        uname = session['username']
    else:
        uname = ""

    return render_template(
        "assess_markedresults.html",
        course=course,
        exam=exam,
        results=results,
        examtotal=examtotal,
        fullname=fullname,
        uname=uname,
        datesubmit=datesubmit,
        datemarked=datemarked
    )

