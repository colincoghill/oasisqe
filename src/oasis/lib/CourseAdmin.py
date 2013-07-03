# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Administration frontend for courses and related areas
"""

import datetime

# from oasis import log, INFO, ERROR

from oasis.lib.Permissions import get_course_perms, add_perm, delete_perm
from oasis.lib.Audit import audit
from oasis.lib import Users2, DB, Topics, General, Exams, Courses


def do_topic_update(course, request):
    """Read the submitted form and make relevant changes to Topic information
    """
    categories = []
    topics = []

    form = request.form
    if form:
        for i in form.keys():
            parts = i.split('_')
            if len(parts) > 1:
                catid = parts[0]
                if catid not in categories:
                    categories = categories + [catid]

        for c in categories:
            topics = topics + [{'id': int(c),
                                'position': form['%s_position' % c],
                                'name': form['%s_name' % c],
                                'visibility': form['%s_visibility' % c]
                                }]
        for i in topics:
            if not i['id'] == 0:
                Topics.set_pos(i['id'], i['position'])
                Topics.set_name(int(i['id']), i['name'])
                Topics.set_vis(i['id'], i['visibility'])
                Courses.incr_version()
            else:
                if not i['name'] == "[Name of new topic]":
                    Topics.create(course['id'],
                                  i['name'],
                                  int(i['visibility']),
                                  i['position'])
                    Courses.incr_version()

        return True

    return False


# This is taken from OaSetupFE, but should probably be moved into the database
# at some point.
def get_perm_short(pid):
    """ Return a short human readable name for the permission."""

    pNames = {
        1: "Super User",
        2: "User Administrator",
        5: "Question Editor",
        8: "View Marks",
        9: "Alter Marks",
        10: "Preview Questions",
        11: "Preview Assessments",
        14: "Create Assessments",
        15: "View Class List",
        16: "Preview Surveys",
        17: "Create Surveys",
        18: "Edit System Messages",
        20: "View Survey Results"
    }

    if pid in pNames:
        return pNames[pid]
    return None


def save_perms(request, cid, user_id):
    """ Save permission changes
    """

    permlist = get_course_perms(cid)
    perms = {}
    users = {}
    for perm in permlist:
        u = Users2.get_user(perm[0])
        uname = u['uname']
        if not uname in users:
            users[uname] = {}
        users[uname]['fullname'] = u['fullname']

        if not uname in perms:
            perms[uname] = []
        perms[uname].append(int(perm[1]))

    form = request.form
    if form:    # we received a form submission, work out changes and save them
        fields = [field for field in form.keys() if field[:5] == "perm_"]
        newperms = {}

        for field in fields:
            uname = field.split('_')[1]
            perm = int(field.split('_')[2])

            if not uname in newperms:
                newperms[uname] = []
            newperms[uname].append(perm)

        for uname in users:
            uid = Users2.uid_by_uname(uname)
            for perm in [2, 5, 10, 14, 11, 8, 9, 15]:
                if uname in newperms and perm in newperms[uname]:
                    if not perm in perms[uname]:
                        add_perm(uid, cid, perm)
                        audit(
                            1,
                            user_id,
                            uid,
                            "CourseAdmin",
                            "%s given %s permission by %s" % (uname, get_perm_short(perm), user_id,)
                        )
                else:
                    if uname in perms and perm in perms[uname]:
                        delete_perm(uid, cid, perm)
                        audit(
                            1,
                            user_id,
                            uid,
                            "CourseAdmin",
                            "%s had %s permission revoked by %s" % (uname, get_perm_short(perm), user_id,)
                        )

        for uname in newperms:
            uid = Users2.uid_by_uname(uname)
            if not uname in perms:
                # We've added a user
                for perm in [2, 5, 10, 14, 11, 8, 9, 15]:
                    if perm in newperms[uname]:
                        add_perm(uid, cid, perm)
                        audit(
                            1,
                            user_id,
                            uid,
                            "CourseAdmin",
                            "%s given %s permission by %s" % (uname, get_perm_short(perm), user_id,)
                        )
        if "adduser" in form:
            newuname = form['adduser']
            newuid = Users2.uid_by_uname(newuname)
            if newuid:
                add_perm(newuid, cid, 10)
            audit(
                1,
                user_id,
                newuid,
                "CourseAdmin",
                "%s given '%s' permission by %s" % (newuname, get_perm_short(10), user_id,)
            )
    return


def exam_edit_submit(request, user_id, cid, exam_id):
    """ Accept the submitted exam edit/create form.
        If exam_id is not provided, create a new one.
    """

    # TODO: More validation. Currently we trust the client validation,
    # although the user is authenticated staff so probably not too high a
    # risk of shenanigans.

    title = str(request.form['assess_title'])
    atype = int(request.form['assess_type'])
    startdate = request.form['startdate']
    starthour = int(request.form['examstart_hour'])
    startmin = int(request.form['examstart_minute'])
    enddate = request.form['enddate']
    endhour = int(request.form['examend_hour'])
    endmin = int(request.form['examend_minute'])
    duration = int(request.form['duration'])
    code = request.form['assess_code']
    instant = int(request.form['assess_instant'])
    if "instructions" in request.form:
        instructions = request.form['instructions']
    else:
        instructions = ""

    astart = datetime.datetime.strptime(startdate, "%a %d %b %Y")
    astart = astart.replace(hour=starthour, minute=startmin)
    aend = datetime.datetime.strptime(enddate, "%a %d %b %Y")
    aend = aend.replace(hour=endhour, minute=endmin)

    qns = {}
    for k in request.form.keys():

        v = request.form.getlist(k)
        if k.startswith("question_"):
            _, q, p = k.split("_")
            if not q in qns:
                qns[q] = []
            if not v[0] == '---':
                qns[q].append(int(v[0]))

    if not exam_id:
        exam_id = Exams.create(cid, user_id, title, atype, duration, astart,
                               aend, instructions, code=code, instant=instant)
    else:  # update
        Exams.set_title(exam_id, title)
        Exams.set_duration(exam_id, duration)
        Exams.set_type(exam_id, atype)
        Exams.set_description(exam_id, instructions)
        Exams.set_start_time(exam_id, astart)
        Exams.set_end_time(exam_id, aend)
        Exams.set_code(exam_id, code)
        Exams.set_instant(exam_id, instant)

    for pos, qts in qns.iteritems():
        if pos:
            DB.update_exam_qt_in_pos(exam_id, int(pos), qts)

    return exam_id


def _get_q_list_sorted(topic):
    # TODO: Is this duplicated elsewhere?
    def cmp_question_position(a, b):
        """Order questions by the absolute value of their positions
           since we use -'ve to indicate hidden.
        """

        return cmp(abs(a['position']), abs(b['position']))

    questionlist = General.get_q_list(topic, None, False)

    if questionlist:
        # At the moment we use -'ve positions to indicate that a question
        # is hidden but when displaying them we want to maintain the sort order.
        for question in questionlist:
            # Usually questions with position 0 are broken or uninteresting
            # so put them at the bottom.
            if question['position'] == 0:
                question['position'] = -10000
        questionlist.sort(cmp_question_position)
    else:
        questionlist = []

    return questionlist


def get_create_exam_q_list(course):
    """ Return a list of questions that can be used to create an assessment
    """

    topics = Courses.get_topics_all(course, archived=0, numq=False)
    for num, topic in topics.iteritems():
        topic_id = topics[num]['id']
        topics[num]['questions'] = _get_q_list_sorted(topic_id)
    return topics

