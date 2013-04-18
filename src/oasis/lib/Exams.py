# -*- coding: utf-8 -*-

""" Exams.py
    Handle exam related database operations.
"""

import time
import json
import datetime
from logging import log, INFO, ERROR

from .OaDB import run_sql, dbpool, MC
from .OaTypes import todatetime
import CourseAPI
from .OaUserDB import checkPermission
import OaDB, OaGeneral


def saveScore(exam, student, examtotal):
    """ Store the exam score.
        Currently puts it into the marklog.
    """
    assert isinstance(exam, int)
    assert isinstance(student, int)
    assert isinstance(examtotal, float) or isinstance(examtotal, int)
    run_sql("""INSERT INTO marklog (eventtime, exam, student, marker, operation, value)
                 VALUES (NOW(), %s, %s, 1, 'Submitted', %s);""",
            (exam, student, "%.1f" % examtotal))
    touchUserExam(exam, student)


def setDuration(exam, duration):
    """ Set the duration of an assessment."""
    assert isinstance(exam, int)
    assert isinstance(duration, int) or isinstance(duration, float)
    run_sql("""UPDATE exams SET duration=%s WHERE exam=%s;""", (duration, exam))


def setInstant(exam, instant):
    """ Set the instant results status of an assessment."""
    assert isinstance(exam, int)
    assert isinstance(instant, int)
    run_sql("""UPDATE exams SET instant=%s WHERE exam=%s;""", (instant, exam))


def getStudentStartTimeString(exam, student):
    """ Return the time the student started an assessment in
        human readable format.
    """
    assert isinstance(exam, int)
    assert isinstance(student, int)
    ret = run_sql("""SELECT MIN(firstview) FROM questions WHERE exam = %s AND student = %s;""", (exam, student))
    if ret:
        firstview = ret[0][0]
        if firstview:
            return firstview.strftime("%Y %b %d %H:%M")
    return None


def getStudentStartTime(exam, student):
    """ Return the time the student started an assessment as
        a datetime object or None
    """
    assert isinstance(exam, int)
    assert isinstance(student, int)
    ret = run_sql("""SELECT firstview FROM questions
                    WHERE exam=%s AND student=%s ORDER BY firstview ASC LIMIT 1;""", (exam, student))
    if ret:
        firstview = ret[0][0]
        if firstview:
            return todatetime(firstview)
    return None


def getMarkTime(exam, student):
    """ Return the time the student submitted an assessment
        Returns a datetime object or None
    """
    assert isinstance(exam, int)
    assert isinstance(student, int)
    ret = run_sql("SELECT marktime FROM questions "
                  "WHERE exam=%s AND student=%s ORDER BY marktime DESC LIMIT 1;", (exam, student))
    if ret:
        lastview = ret[0][0]
        if lastview:
            return todatetime(lastview)
    return None


def getMarkDate(user, exam):
    """ Fetch the most recent mark date of an exam. """
    assert isinstance(exam, int)
    assert isinstance(user, int)
    ret = run_sql("""SELECT eventtime FROM marklog WHERE exam=%s AND student=%s;""", (exam, user))
    if ret:
        return ret[len(ret) - 1][0]
    return "notmarked"


def setType(exam, examtype):
    """ Set the type of an assessment."""
    assert isinstance(exam, int)
    assert isinstance(examtype, int)
    run_sql("""UPDATE exams SET "type"=%s WHERE exam=%s;""", (examtype, exam,))


def setTitle(exam, title):
    """ Set the title of an assessment. """
    assert isinstance(exam, int)
    assert isinstance(title, str) or isinstance(title, unicode)
    run_sql("""UPDATE exams SET title=%s WHERE exam=%s;""", (title, exam))


def setCode(exam, code):
    """ Set the code of an assessment. """
    assert isinstance(exam, int)
    assert isinstance(code, str) or isinstance(code, unicode)
    run_sql("""UPDATE exams SET code=%s WHERE exam=%s;""", (code, exam))


def getStartEpoch(exam):
    """ Fetch the start time of an assessment as an EPOCH float"""
    assert isinstance(exam, int)
    key = "exams-%d-startepoch" % exam
    obj = MC.get(key)
    if not obj is None:
        return obj
    sql = 'SELECT EXTRACT(EPOCH FROM "start") FROM exams WHERE exam = %s;'
    params = (exam,)
    ret = run_sql(sql, params)
    if ret:
        MC.set(key, float(ret[0][0]))
        return float(ret[0][0])
    log(ERROR, "Request for unknown exam %s." % exam)
    return None


def getSubmitTime(exam, student):
    """ Return the time the exam was submitted for marking.
        Returns a datetime object or None
    """
    assert isinstance(exam, int)
    assert isinstance(student, int)
    submittime = None
    res = run_sql("SELECT submittime FROM userexams WHERE exam = %s AND student = %s;", (exam, student))
    if res:
        submittime = res[0][0]
    if submittime is None:
        return None
    return todatetime(submittime)


def getStudents(exam):
    """ Return a list of students who have done the exam."""
    assert isinstance(exam, int)
    res = run_sql("""SELECT student FROM examquestions WHERE exam=%s GROUP BY student;""", (exam,))
    students = []
    if res:
        for row in res:
            students.append(int(row[0]))
    return students


def isDoneBy(user, exam):
    """ Return True if the user has submitted the exam. We currently look for an entry in marklog."""
    assert isinstance(user, int)
    assert isinstance(exam, int)
    ret = run_sql("""SELECT marker FROM marklog WHERE exam=%s AND student=%s;""", (exam, user))
    # FIXME:  This can now be handled by the userexams status, but since we have a lot of old data
    # that hasn't been updated we need to stay doing this the old way for now.
    if ret:
        return True
    return False


def getUserStatus(student, exam):
    """ Returns the status of the particular exam instance.
        -1 = instance not found
        0 = not generated
        1 = unseen
        2 = started
        3 = out of time
        4 = submitted, not marked
        5 = marked, preliminary
        6 = marked, official
        7 = broken (will be hidden)
    """
    assert isinstance(student, int)
    assert isinstance(exam, int)
    res = run_sql("""SELECT status FROM userexams WHERE exam=%s AND student=%s;""", (exam, student))
    if res:
        return int(res[0][0])
    log(ERROR, "Unable to get user %s status for exam %s! " % (student, exam))
    return -1


def setUserStatus(student, exam, status):
    """ Set the status of a particular exam instance. """
    assert isinstance(student, int)
    assert isinstance(exam, int)
    assert isinstance(status, int)
    prevstatus = getUserStatus(student, exam)
    if prevstatus <= 0:
        createUserExam(student, exam)
    run_sql("""UPDATE userexams SET status=%s WHERE exam=%s AND student=%s;""", (status, exam, student))
    newstatus = getUserStatus(student, exam)
    if not newstatus == status:
        log(ERROR, "Failed to set new status:  setUserStatus(%s, %s, %s)" % (student, exam, status))
    touchUserExam(exam, student)


def createUserExam(student, exam):
    """ Create a new instance of an exam for a student."""
    assert isinstance(student, int)
    assert isinstance(exam, int)
    status = getUserStatus(student, exam)
    if status == -1:
        run_sql("""INSERT INTO userexams (exam, student, status, score)
                    VALUES (%s, %s, '1', '-1'); """, (exam, student))


def create(course, owner, title, examtype, duration, start, end, instructions, code=None, instant=1):
    """ Add an assessment to the database."""
    assert isinstance(course, int)
    assert isinstance(owner, int)
    assert isinstance(title, str) or isinstance(title, unicode)
    assert isinstance(examtype, int)
    assert isinstance(duration, int) or isinstance(duration, float)
    assert isinstance(start, datetime.datetime) or isinstance(start, str) or isinstance(start, unicode)
    assert isinstance(end, datetime.datetime) or isinstance(end, str) or isinstance(end, unicode)
    assert isinstance(instructions, str) or isinstance(instructions, unicode)
    assert isinstance(code, str) or isinstance(code, unicode) or code is None
    assert isinstance(instant, int)
    conn = dbpool.begin()
    sql = """INSERT INTO exams (title, owner, type, start, "end", description, course, duration, code, instant)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
    params = (title, owner, examtype, start, end, instructions, course, duration, code, instant)
    log(INFO, "Create Exam on course %s: [%s][%s]" % (course, sql, params))
    conn.run_sql(sql, params)
    res = conn.run_sql("SELECT currval('exams_exam_seq')")
    dbpool.commit(conn)
    if res:
        return int(res[0][0])
    log(ERROR, "Create exam FAILED on course %s: [%s][%s]" % (course, sql, params))
    return 0


def setDescription(exam, description):
    """ Set the description of an assessment."""
    assert isinstance(exam, int)
    assert isinstance(description, str) or isinstance(description, unicode)
    run_sql("""UPDATE exams SET description=%s WHERE exam=%s;""", (description, exam))


def getEndTime(exam, user):
    """ Return the time that an exam ends for the given user. """
    assert isinstance(exam, int)
    assert isinstance(user, int)
    ret = run_sql("""SELECT endtime FROM examtimers WHERE exam=%s AND userid=%s;""", (exam, user))
    if ret:
        return float(ret[0][0])
    ret = run_sql("SELECT duration FROM exams where exam=%s;", (exam,))
    duration = int(ret[0][0])
    nowtime = time.time()
    endtime = nowtime + (duration * 60)
    run_sql("""INSERT INTO examtimers (userid, exam, endtime)
               VALUES (%s, %s, %s)""", (user, exam, endtime))
    return float(endtime)


def setEnd(exam, examend):
    """ Set the end time of an assessment. """
    assert isinstance(exam, int)
    assert isinstance(examend, datetime.datetime) or isinstance(examend, str) or isinstance(examend, unicode)
    key = "exams-%d-endepoch" % exam
    MC.delete(key)
    run_sql("""UPDATE exams SET "end"=%s WHERE exam=%s;""", (examend, exam))


def setStart(exam, examstart):
    """ Set the start time of an assessment."""
    assert isinstance(exam, int)
    assert isinstance(examstart, datetime.datetime) or isinstance(examstart, str) or isinstance(examstart, unicode)
    key = "exams-%d-startepoch" % exam
    MC.delete(key)
    run_sql("""UPDATE exams SET "start"=%s WHERE exam=%s;""", (examstart, exam))


def getMarker(user, exam):
    """ Fetch the most recent marker of an exam. """
    assert isinstance(exam, int)
    assert isinstance(user, int)
    ret = run_sql("""SELECT eventtime, marker FROM marklog WHERE exam=%s AND student=%s;""", (exam, user))
    if ret:
        return int(ret[len(ret) - 1][1])
    log(ERROR, "Request for unknown exam %s/user %s." % (user, exam))
    return None


def getMarkTotal(user, exam):
    """ Fetch the most recent total mark."""
    assert isinstance(exam, int)
    assert isinstance(user, int)
    ret = run_sql("""SELECT eventtime, total FROM marklog WHERE exam=%s AND student=%s;""", (exam, user))
    if ret:
        return float(ret[len(ret) - 1][1])
    log(ERROR, "Request for unknown exam %s/user %s." % (user, exam))
    return None


def getNumQuestions(exam):
    """ Return the number of questions in the exam."""
    assert isinstance(exam, int)
    ret = run_sql("""SELECT position FROM examqtemplates WHERE exam=%s GROUP BY position;""", (exam,))
    if ret:
        return len(ret)
    log(ERROR, "Request for unknown exam %s" % exam)
    return 0


def getExamsDone(user):
    """ Return a list of assessments done by the user."""
    assert isinstance(user, int)
    ret = run_sql("SELECT exam FROM examquestions WHERE student = %s GROUP BY exam", (user,))
    if not ret:
        return []
    exams = [int(row[0]) for row in ret]
    return exams


def logMark(exam, marking, student, position, qtemplate, question,
            part, marker, manual, official, operation, new, score):
    """ Record the mark for the given exam question.
        If "marking" is None, also assign a new marking value and
        return it so it can be passed in next time.
    """
    assert isinstance(exam, int)
    assert isinstance(marking, int)
    assert isinstance(student, int)
    assert isinstance(position, int)
    assert isinstance(qtemplate, int)
    assert isinstance(question, int)
    assert isinstance(part, int)
    assert isinstance(marker, int)
    assert isinstance(official, int)
    assert isinstance(operation, int)
    assert isinstance(new, int)
    assert isinstance(score, int) or isinstance(score, float)
    if not marking:
        sql = """SELECT max(marking) FROM marks;"""
        res = run_sql(sql)
        try:
            marking = int(res[0][0])
            marking += 1
        except (ValueError, TypeError, IndexError, KeyError):
            marking = 1

    if manual:
        manual = 'yes'
    else:
        manual = 'no'
    if official:
        official = 'yes'
    else:
        official = 'no'
    if new:
        new = 'yes'
    else:
        new = 'no'
    sql = """INSERT INTO marks (eventtime, exam, marking, student, position,
                                qtemplate, question, part, marker, manual,
                                official, operation, changed, score)
            VALUES (NOW(), %s, %s, %s, %s,
                     %s, %s, %s, %s, %s,
                     %s, %s, %s, %s);"""

    run_sql(sql, (exam, marking, student, position, qtemplate, question,
                  part, marker, manual, official, operation, new, score))
    touchUserExam(exam, student)
    return marking


def getAnswersForPart(exam, qtid, part, group=None):
    """ Returns a list of all answers given for a particular question template part.
        If group is given, will only return answers for users in that group.
    """
    assert isinstance(exam, int)
    assert isinstance(qtid, int)
    assert isinstance(part, int)
    assert isinstance(group, int) or group is None
    if group is None:
        sql = """select guesses.guess
                from userexams, users, questions, guesses
                where userexams.exam=%s
                and users.id=userexams.student
                and questions.exam=%s
                and questions.question = guesses.question
                and questions.student=userexams.student
                and guesses.part=%s
                and questions.qtemplate=%s"""
        params = (exam, exam, part, qtid)
    else:
        sql = """select guesses.guess
                from userexams, users, questions, guesses, usergroups
                where userexams.exam=%s
                and users.id=userexams.student
                and questions.exam=%s
                and questions.question = guesses.question
                and questions.student=userexams.student
                and guesses.part=%s and questions.qtemplate=%s
                and usergroups.userid=userexams.student
                and usergroups.groupid=%s"""
        params = (exam, exam, part, qtid, group)

    ret = run_sql(sql, params)
    if ret:
        answers = [row[0] for row in ret]
        return answers
    return []


def setSubmitTime(student, exam, submittime=None):
    """Set the submit time of the exam instance to a given time, or NOW() """
    assert isinstance(student, int)
    assert isinstance(exam, int)
    assert isinstance(submittime, datetime.datetime) or submittime is None
    if submittime:
        run_sql("""UPDATE userexams SET submittime=%s WHERE exam=%s AND student=%s;""", (submittime, exam, student))
    else:
        run_sql("""UPDATE userexams SET submittime=NOW() WHERE exam=%s AND student=%s;""", (exam, student))
    touchUserExam(exam, student)


# FIXME: watch for memcache issues.
def resetEndTime(exam, user):
    """ Reset the Exam timer for the student. This should let them resit the exam. """
    assert isinstance(exam, int)
    assert isinstance(user, int)
    run_sql("DELETE FROM examtimers WHERE exam=%s AND userid=%s;", (exam, user))
    log(INFO, "Exam %s timer reset for user %s" % (exam, user))
    touchUserExam(exam, user)


def resetSubmitTime(exam, user):
    """ Reset the Exam submit time for the student. This should let them resit
        the exam.
    """
    assert isinstance(exam, int)
    assert isinstance(user, int)
    sql = "UPDATE userexams SET submittime = NULL WHERE exam=%s AND student=%s;"
    params = (exam, user)
    run_sql(sql, params)
    log(INFO, "Exam %s submit time reset for user %s" % (exam, user))
    touchUserExam(exam, user)


def touchUserExam(exam, user):
    """ Update the lastchange field on a user exam so other places can tell that
        something changed. This should probably be done any time one of the
        following changes:
            userexam fields on that row
            question/guess in the exam changes
    """
    assert isinstance(exam, int)
    assert isinstance(user, int)
    OaDB.touchUserExam(exam, user)


def resetMark(exam, user):
    """ Remove the final mark for the student. This should let them resit the exam. """
    assert isinstance(exam, int)
    assert isinstance(user, int)
    run_sql("DELETE FROM marklog WHERE exam=%s AND student=%s;", (exam, user))
    log(INFO, "Exam %s mark reset for user %s" % (exam, user))
    touchUserExam(exam, user)


def getQuestionMarks(group, exam, qtemplate):
    """ get the marks for a particular question template from an exam """
    assert isinstance(exam, int)
    assert isinstance(group, int)
    assert isinstance(qtemplate, int)
    ret = run_sql("""SELECT
                        score, COUNT(score)
                FROM
                        questions
                WHERE
                        qtemplate=%s
                AND
                        marktime < NOW()
                AND
                        exam > 0
                AND
                        question in
                (SELECT question from examquestions WHERE exam=%s)
                AND
                        student in
                (SELECT userid FROM usergroups WHERE groupid=%s)

        GROUP BY
                        score
        ORDER BY
                        score
        ;
        """, (qtemplate, exam, group))
    if ret:
        return ret


def getQTemplates(exam):
    """Return an ordered list of qtemplates used in the exam. """
    assert isinstance(exam, int)
    ret = run_sql("""SELECT position, qtemplate FROM examqtemplates WHERE exam=%s ORDER BY position;""", (exam,))
    if ret:
        return [int(row[1]) for row in ret]
    log(ERROR, "Request for unknown exam %s or exam has no qtemplates." % exam)
    return []


def getQTemplatesInfo(exam):
    """Return information about the qtemplates used in the exam as a dictionary, keyed by position."""
    assert isinstance(exam, int)
    ret = run_sql("""SELECT examqtemplates.qtemplate, examqtemplates.position, qtemplates.title,
                            questiontopics.topic, questiontopics.position
                     FROM examqtemplates, qtemplates, questiontopics
                     WHERE examqtemplates.qtemplate=qtemplates.qtemplate
                        AND questiontopics.qtemplate=examqtemplates.qtemplate
                        AND examqtemplates.exam=%s
                     ORDER BY examqtemplates.position;""", (exam,))
    positions = {}
    if ret:
        position = None
        for row in ret:
            if not position == int(row[1]):
                position = int(row[1])
                positions[position] = []
            positions[position].append({'id': int(row[0]), 'name': row[2],
                                        'position': int(row[1]), 'topic': int(row[3]),
                                        'topicposition': int(row[4])})
    return positions


def getQTemplatesList(exam):
    """Return a list of qtemplates used in the exam."""
    assert isinstance(exam, int)
    ret = run_sql("""SELECT examqtemplates.qtemplate, examqtemplates.position, qtemplates.title,
                            questiontopics.topic, questiontopics.position
                     FROM examqtemplates, qtemplates, questiontopics
                     WHERE examqtemplates.qtemplate=qtemplates.qtemplate
                       AND questiontopics.qtemplate=examqtemplates.qtemplate
                       AND examqtemplates.exam=%s
                     ORDER BY examqtemplates.position;""", (exam,))
    positions = {}
    if ret:
        position = None
        for row in ret:
            if not position == int(row[1]):
                position = int(row[1])
                positions[position] = []
            positions[position].append({'id': int(row[0]),
                                        'name': row[2],
                                        'position': int(row[1]),
                                        'topic': int(row[3]),
                                        'topicposition': int(row[4])})
    return [positions[p] for p in positions.keys()]


def getNumDone(exam, group=None):
    """Return the number of exams completed by the given group"""
    assert isinstance(exam, int)
    assert isinstance(group, int) or group is None
    if group:
        sql = """SELECT count(userexams.status)
                FROM userexams,usergroups
                WHERE userexams.student = usergroups.userid
                AND usergroups.groupid = %s
                AND exam = %s
                AND status >= 4
                AND status <=6;"""
        params = (group, exam)
    else:
        sql = "SELECT count(status) FROM userexams WHERE exam = %s AND status >= 4 AND status <=6;"
        params = (exam, )

    ret = run_sql(sql, params)
    if not ret:
        return 0
    return int(ret[0][0])


def unsubmit(exam, student):
    """ Undo the submission of an exam and reset the timer. """
    assert isinstance(exam, int)
    assert isinstance(student, int)
    resetMark(exam, student)
    resetEndTime(exam, student)
    resetSubmitTime(exam, student)
    setUserStatus(student, exam, 1)
    touchUserExam(exam, student)


def setMarkStatus(exam, status):
    """ Set the marking status of the exam.
        see getMarkStatus for values.
    """
    assert isinstance(exam, int)
    assert isinstance(status, int)
    run_sql("""UPDATE exams SET markstatus=%s WHERE exam=%s;""", (status, exam))


def _serialize_examstruct(exam):
    """ Serialize the exam structure for, eg. cache.
        The dates, especially, need work before JSON
    """
    assert isinstance(exam, dict)
    FMT = '%Y-%m-%d %H:%M:%S'
    assert isinstance(exam['start'], datetime.datetime)
    assert isinstance(exam['end'], datetime.datetime)
    safe = exam.copy()
    safe['start'] = exam['start'].strftime(FMT)
    safe['end'] = exam['end'].strftime(FMT)

    return json.dumps(safe)


def _deserialize_examstruct(obj):
    """ Deserialize a serialized exam structure. """
    assert isinstance(obj, str) or isinstance(obj, unicode)
    FMT = '%Y-%m-%d %H:%M:%S'
    exam = json.loads(obj)
    exam['start'] = datetime.datetime.strptime(exam['start'], FMT)
    exam['end'] = datetime.datetime.strptime(exam['end'], FMT)

    assert isinstance(exam['start'], datetime.datetime)
    assert isinstance(exam['end'], datetime.datetime)
    return exam


# TODO: Optimize. This is called quite a lot
def getExamStruct(exam_id, user_id=None, include_qtemplates=False, include_stats=False):
    """ Return a dictionary of useful data about the given exam for the given user.
        Including stats is a performance hit so don't unless you need them.
    """
    assert isinstance(exam_id, int)
    assert isinstance(user_id, int) or user_id is None
    assert isinstance(include_qtemplates, bool)
    assert isinstance(include_stats, bool)
    key = "exam-%s-struct" % exam_id
    obj = MC.get(key)
    if obj:
        exam = _deserialize_examstruct(obj)
    else:
        sql = """SELECT "title", "owner", "type", "start", "end",
                        "description", "comments", "course", "archived",
                        "duration", "markstatus", "instant", "code"
                 FROM "exams" WHERE "exam" = %s LIMIT 1;"""
        params = (exam_id, )
        ret = run_sql(sql, params)
        if not ret:
            raise KeyError("Exam %s not found." % exam_id)
        row = ret[0]
        exam = {'id': exam_id,
                'title': row[0],
                'owner': row[1],
                'type': row[2],
                'start': row[3],
                'end': row[4],
                'instructions': row[5],
                'comments': row[6],
                'cid': row[7],
                'archived': row[8],
                'duration': row[9],
                'markstatus': row[10],
                'instant': row[11],
                'code': row[12]
        }

        MC.set(key, _serialize_examstruct(exam),
               60) # 60 second cache. enough to take the edge off an exam start peak load
    course = CourseAPI.getCourse(exam['cid'])
    exam['future'] = OaGeneral.isFuture2(exam['start'])
    exam['past'] = OaGeneral.isPast2(exam['end'])
    exam['soon'] = OaGeneral.isSoon(exam['start'])
    exam['recent'] = OaGeneral.isRecent(exam['end'])
    exam['active'] = OaGeneral.isNow(exam['start'], exam['end'])
    exam['start_epoch'] = int(exam['start'].strftime("%s"))  # useful for sorting
    exam['period'] = OaGeneral.humanDatePeriod(exam['start'], exam['end'])
    exam['course'] = course
    exam['start_human'] = exam['start'].strftime("%a %d %b")

    if include_qtemplates:
        exam['qtemplates'] = getQTemplates(exam_id)
        exam['num_questions'] = len(exam['qtemplates'])
    if include_stats:
        exam['coursedone'] = getNumDone(exam_id, exam['cid'])
        exam['notcoursedone'] = getNumDone(exam_id), exam['coursedone']
    if user_id:
        exam['is_done'] = isDoneBy(user_id, exam_id)
        exam['can_preview'] = checkPermission(user_id, exam['cid'], "OASIS_PREVIEWASSESSMENT")

    return exam
