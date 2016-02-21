# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Exams.py
    Handle exam related database operations.
"""

import time
import json
import datetime

from .DB import run_sql, MC
from .OaTypes import todatetime
from .Permissions import check_perm
import DB
import General
import Courses
from logging import getLogger

L = getLogger("oasisqe")


def save_score(exam_id, student, examtotal):
    """ Store the exam score.
        Currently puts it into the marklog.
    """
    assert isinstance(exam_id, int)
    assert isinstance(student, int)
    assert isinstance(examtotal, float) or isinstance(examtotal, int)
    L.info("Saving exam score %s for user %s, exam %s" % (examtotal, student, exam_id))
    run_sql("""INSERT INTO marklog (eventtime, exam, student, marker, operation, value)
                 VALUES (NOW(), %s, %s, 1, 'Submitted', %s);""",
            (exam_id, student, "%.1f" % examtotal))
    touchuserexam(exam_id, student)


def set_duration(exam_id, duration):
    """ Set the duration of an assessment."""
    assert isinstance(exam_id, int)
    assert isinstance(duration, int) or isinstance(duration, float)
    run_sql("""UPDATE exams SET duration=%s WHERE exam=%s;""",
            (duration, exam_id))


def set_instant(exam_id, instant):
    """ Set the instant results status of an assessment."""
    assert isinstance(exam_id, int)
    assert isinstance(instant, int)
    run_sql("""UPDATE exams SET instant=%s WHERE exam=%s;""",
            (instant, exam_id))


def get_student_start_time(exam, student):
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


def get_mark_time(exam, student):
    """ Return the time the student submitted an assessment
        Returns a datetime object or None
    """
    assert isinstance(exam, int)
    assert isinstance(student, int)
    ret = run_sql("""SELECT marktime
                     FROM questions
                     WHERE exam=%s
                       AND student=%s
                     ORDER BY marktime DESC
                     LIMIT 1;""", (exam, student))
    if ret:
        lastview = ret[0][0]
        if lastview:
            return todatetime(lastview)
    return None


def set_type(exam, examtype):
    """ Set the type of an assessment."""
    assert isinstance(exam, int)
    assert isinstance(examtype, int)
    run_sql("""UPDATE exams SET "type"=%s WHERE exam=%s;""", (examtype, exam,))


def set_title(exam, title):
    """ Set the title of an assessment. """
    assert isinstance(exam, int)
    assert isinstance(title, str) or isinstance(title, unicode)
    run_sql("""UPDATE exams SET title=%s WHERE exam=%s;""", (title, exam))


def set_code(exam, code):
    """ Set the code of an assessment. """
    assert isinstance(exam, int)
    assert isinstance(code, str) or isinstance(code, unicode)
    run_sql("""UPDATE exams SET code=%s WHERE exam=%s;""", (code, exam))


def get_submit_time(exam_id, student):
    """ Return the time the exam was submitted for marking.
        Returns a datetime object or None
    """
    assert isinstance(exam_id, int)
    assert isinstance(student, int)
    submittime = None
    res = run_sql("SELECT submittime FROM userexams WHERE exam = %s AND student = %s;",
                  (exam_id, student))
    if res:
        submittime = res[0][0]
    if submittime is None:
        return None
    return todatetime(submittime)


def is_done_by(user, exam):
    """ Return True if the user has submitted the exam. We currently look for an entry in marklog."""
    assert isinstance(user, int)
    assert isinstance(exam, int)
    ret = run_sql("SELECT marker FROM marklog WHERE exam=%s AND student=%s;",
                  (exam, user))
    # FIXME:  This can now be handled by the userexams status, but since
    # we have a lot of old data that hasn't been updated we need to stay
    # doing this the old way for now.
    if ret:
        return True
    return False


def get_user_status(student, exam):
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
    L.error("Unable to get user %s status for exam %s! " % (student, exam))
    return -1


def set_user_status(student, exam, status):
    """ Set the status of a particular exam instance. """
    assert isinstance(student, int)
    assert isinstance(exam, int)
    assert isinstance(status, int)
    prevstatus = get_user_status(student, exam)
    if prevstatus <= 0:
        create_user_exam(student, exam)
    run_sql("""UPDATE userexams SET status=%s WHERE exam=%s AND student=%s;""", (status, exam, student))
    newstatus = get_user_status(student, exam)
    if not newstatus == status:
        L.error("Failed to set new status:  setUserStatus(%s, %s, %s)" % (student, exam, status))
    touchuserexam(exam, student)


def create_user_exam(student, exam):
    """ Create a new instance of an exam for a student."""
    assert isinstance(student, int)
    assert isinstance(exam, int)
    status = get_user_status(student, exam)
    if status == -1:
        run_sql("""INSERT INTO userexams (exam, student, status, score)
                    VALUES (%s, %s, '1', '-1'); """, (exam, student))


def create(course, owner, title, examtype, duration, start, end,
           instructions, code=None, instant=1):
    """ Add an assessment to the database."""
    assert isinstance(course, int)
    assert isinstance(owner, int)
    assert isinstance(title, str) \
        or isinstance(title, unicode)
    assert isinstance(examtype, int)
    assert isinstance(duration, int) \
        or isinstance(duration, float)
    assert isinstance(start, datetime.datetime) \
        or isinstance(start, str) \
        or isinstance(start, unicode)
    assert isinstance(end, datetime.datetime) \
        or isinstance(end, str) \
        or isinstance(end, unicode)
    assert isinstance(instructions, str) \
        or isinstance(instructions, unicode)
    assert isinstance(code, str) \
        or isinstance(code, unicode) \
        or code is None
    assert isinstance(instant, int)
    sql = """INSERT INTO exams (title, owner, type, start, "end", description,
                                course, duration, code, instant)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING exam;"""
    params = (title, owner, examtype, start, end, instructions,
              course, duration, code, instant)
    L.info("Create Exam on course %s: [%s][%s]" % (course, sql, params))
    res = run_sql(sql, params)
    if res:
        return int(res[0][0])
    L.error("Create exam FAILED on course %s: [%s][%s]" % (course, sql, params))
    return 0


def set_description(exam_id, description):
    """ Set the description of an assessment."""
    assert isinstance(exam_id, int)
    assert isinstance(description, str) or isinstance(description, unicode)
    run_sql("""UPDATE exams SET description=%s WHERE exam=%s;""",
            (description, exam_id))


def get_end_time(exam, user):
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


def set_end_time(exam, examend):
    """ Set the end time of an assessment. """
    assert isinstance(exam, int)
    assert isinstance(examend, datetime.datetime) or isinstance(examend, str) or isinstance(examend, unicode)
    key = "exams-%d-endepoch" % exam
    MC.delete(key)
    run_sql("""UPDATE exams SET "end"=%s WHERE exam=%s;""", (examend, exam))


def set_start_time(exam, examstart):
    """ Set the start time of an assessment."""
    assert isinstance(exam, int)
    assert isinstance(examstart, datetime.datetime) or isinstance(examstart, str) or isinstance(examstart, unicode)
    key = "exams-%d-startepoch" % exam
    MC.delete(key)
    run_sql("""UPDATE exams SET "start"=%s WHERE exam=%s;""", (examstart, exam))


def get_num_questions(exam_id):
    """ Return the number of questions in the exam."""
    assert isinstance(exam_id, int)
    ret = run_sql("""SELECT position FROM examqtemplates WHERE exam=%s GROUP BY position;""", (exam_id,))
    if ret:
        return len(ret)
    L.error("Request for unknown exam %s" % exam_id)
    return 0


def get_exams_done(user):
    """ Return a list of assessments done by the user."""
    assert isinstance(user, int)
    ret = run_sql("SELECT exam FROM examquestions WHERE student = %s GROUP BY exam", (user,))
    if not ret:
        return []
    exams = [int(row[0]) for row in ret]
    return exams


def set_submit_time(student, exam, submittime=None):
    """Set the submit time of the exam instance to a given time, or NOW() """
    assert isinstance(student, int)
    assert isinstance(exam, int)
    assert isinstance(submittime, datetime.datetime) or submittime is None
    L.info("Setting exam submit time to %s for user %s exam %s" % (submittime, student, exam))
    if submittime:
        run_sql("""UPDATE userexams SET submittime=%s WHERE exam=%s AND student=%s;""", (submittime, exam, student))
    else:
        run_sql("""UPDATE userexams SET submittime=NOW() WHERE exam=%s AND student=%s;""", (exam, student))
    touchuserexam(exam, student)


# FIXME: watch for memcache issues.
def reset_end_time(exam, user):
    """ Reset the Exam timer for the student. This should let them resit the exam. """
    assert isinstance(exam, int)
    assert isinstance(user, int)
    run_sql("DELETE FROM examtimers WHERE exam=%s AND userid=%s;", (exam, user))
    L.info("Exam %s timer reset for user %s" % (exam, user))
    touchuserexam(exam, user)


def reset_submit_time(exam, user):
    """ Reset the Exam submit time for the student. This should let them resit
        the exam.
    """
    assert isinstance(exam, int)
    assert isinstance(user, int)
    sql = "UPDATE userexams SET submittime = NULL WHERE exam=%s AND student=%s;"
    params = (exam, user)
    run_sql(sql, params)
    L.info("Exam %s submit time reset for user %s" % (exam, user))
    touchuserexam(exam, user)


def touchuserexam(exam, user):
    """ Update the lastchange field on a user exam so other places can tell that
        something changed. This should probably be done any time one of the
        following changes:
            userexam fields on that row
            question/guess in the exam changes
    """
    assert isinstance(exam, int)
    assert isinstance(user, int)
    DB.touch_user_exam(exam, user)


def reset_mark(exam, user):
    """ Remove the final mark for the student.
        This should let them resit the exam.
    """
    assert isinstance(exam, int)
    assert isinstance(user, int)
    run_sql("DELETE FROM marklog WHERE exam=%s AND student=%s;", (exam, user))
    L.info("Exam %s mark reset for user %s" % (exam, user))
    touchuserexam(exam, user)


def get_qts(exam):
    """Return an ordered list of qtemplates used in the exam. """
    assert isinstance(exam, int)
    ret = run_sql("""SELECT position, qtemplate FROM examqtemplates WHERE exam=%s ORDER BY position;""", (exam,))
    if ret:
        return [int(row[1]) for row in ret]
    L.error("Request for unknown exam %s or exam has no qtemplates." % exam)
    return []


def get_qts_list(exam):
    """Return a list of qtemplates used in the exam."""
    assert isinstance(exam, int)
    ret = run_sql("""SELECT examqtemplates.qtemplate, examqtemplates.position,
                            qtemplates.title, questiontopics.topic,
                            questiontopics.position
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


def get_num_done(exam, group=None):
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
    reset_mark(exam, student)
    reset_end_time(exam, student)
    reset_submit_time(exam, student)
    set_user_status(student, exam, 1)
    touchuserexam(exam, student)


def set_mark_status(exam, status):
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
    date_fmt = '%Y-%m-%d %H:%M:%S'
    assert isinstance(exam['start'], datetime.datetime)
    assert isinstance(exam['end'], datetime.datetime)
    safe = exam.copy()
    safe['start'] = exam['start'].strftime(date_fmt)
    safe['end'] = exam['end'].strftime(date_fmt)

    return json.dumps(safe)


def _deserialize_examstruct(obj):
    """ Deserialize a serialized exam structure. """
    assert isinstance(obj, str) or isinstance(obj, unicode)
    date_fmt = '%Y-%m-%d %H:%M:%S'
    exam = json.loads(obj)
    exam['start'] = datetime.datetime.strptime(exam['start'], date_fmt)
    exam['end'] = datetime.datetime.strptime(exam['end'], date_fmt)

    assert isinstance(exam['start'], datetime.datetime)
    assert isinstance(exam['end'], datetime.datetime)
    return exam


# TODO: Optimize. This is called quite a lot
def get_exam_struct(exam_id, user_id=None, include_qtemplates=False,
                    include_stats=False):
    """ Return a dictionary of useful data about the given exam for the user.
        Including stats is a performance hit so don't unless you need them.
    """
    assert isinstance(exam_id, int)
    assert isinstance(user_id, int) \
        or user_id is None
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
               60)  # 60 second cache. to take the edge off exam start peak load
    course = Courses.get_course(exam['cid'])
    exam['future'] = General.is_future(exam['start'])
    exam['past'] = General.is_past(exam['end'])
    exam['soon'] = General.is_soon(exam['start'])
    exam['recent'] = General.is_recent(exam['end'])
    exam['active'] = General.is_now(exam['start'], exam['end'])
    exam['start_epoch'] = int(exam['start'].strftime("%s"))  # used to sort
    exam['period'] = General.human_dates(exam['start'], exam['end'])
    exam['course'] = course
    exam['start_human'] = exam['start'].strftime("%a %d %b")

    if include_qtemplates:
        exam['qtemplates'] = get_qts(exam_id)
        exam['num_questions'] = len(exam['qtemplates'])
    if include_stats:
        exam['coursedone'] = get_num_done(exam_id, exam['cid'])
        exam['notcoursedone'] = get_num_done(exam_id), exam['coursedone']
    if user_id:
        exam['is_done'] = is_done_by(user_id, exam_id)
        exam['can_preview'] = check_perm(user_id, exam['cid'], "exampreview")

    return exam


def get_marks(group, exam_id):
    """ Fetch the marks for a given user group.
    """
    sql = """
        SELECT u.id, q.qtemplate, q.score, q.firstview, q.marktime
        FROM users AS u,
             questions AS q,
             usergroups AS ug
        WHERE u.id = ug.userid
          AND ug.groupid = %s
          AND u.id = q.student
          AND q.exam = %s;
    """
    params = (group.id, exam_id)
    ret = DB.run_sql(sql, params)
    results = {}
    for row in ret:
        user_id = row[0]
        if user_id not in results:
            results[user_id] = {}
        qtemplate = row[1]
        results[user_id][qtemplate] = {
            'score': row[2],
            'firstview': row[3],
            'marktime': row[4]
        }

    return results
