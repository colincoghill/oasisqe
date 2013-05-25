# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Administration frontend for courses and related areas
"""

import datetime

from oasis.lib.OaUserDB import getCoursePerms, addPerm, deletePerm
from oasis.lib.Audit import audit
from oasis.lib import UserAPI, OaDB, Topics, OaGeneral, Exams, Courses


def doCourseTopicUpdate(course, request):
    """Read the user submitted form and make relevant changes to the Topic information
    """

    categories = []
    categorylist = []

    form = request.form
    if form:
        for i in form.keys():
            parts = i.split('_')
            if len(parts) > 1:
                catid = parts[0]
                if catid not in categories:
                    categories = categories + [catid]

        for c in categories:
            categorylist = categorylist + [{'id': int(c),
                                            'position': form['%s_position' % c],
                                            'name': form['%s_name' % c],
                                            'visibility': form['%s_visibility' % c]
                                           }]
        for i in categorylist:
            if not i['id'] == 0:
                Topics.setPosition(i['id'], i['position'])
                Topics.setName(int(i['id']), i['name'])
                Topics.setVisibility(i['id'], i['visibility'])
                Courses.incrementVersion()
            else:
                if not i['name'] == "[Name of new topic]":
                    Topics.create(course['id'], i['name'], int(i['visibility']), i['position'])
                    Courses.incrementVersion()

        return True

    return False

#
# def _getExamsMarksDownload(cid, eid, formdata):
#     """ Provide a spreadsheet containing all exam marks.
#         fmt should be 'csv' for now.
#         Send a text/csv file with the following columns:
#         groupname, studentID, totalmark, flags
#     """
#
#     out = ""
#     # Info about students in the course
#     userlist = Courses.getUsersInCourse(cid)
#
#     users = {}
#     for user in userlist:
#         users[user] = {'uname': Users.getUname(user),
#                        'givenname': Users.getGivenName(user),
#                        'familyname': Users.getFamilyName(user)
#                        }
#
#     groups = [{'id': gid,
#                'name': Groups.getName(gid),
#                'marks': OaGeneralBE.getGroupExamResults(gid, eid)
#                } for gid in Courses.getGroupsInCourse(cid) ]
#
#     if "showid" in formdata:
#         out += "#ID,"
#     if "showuname" in formdata:
#         out += "#Uname,"
#     if "showname" in formdata:
#         out += "#Family Name,#Given Name,"
#     if "showparts" in formdata:
#         numparts = Exams.getNumQuestions(eid)
#         for part in range(1,numparts+1):
#             out += "#Q%d," % (part,)
#     if "showmark" in formdata:
#         out += "#Mark,"
#     if "showduration" in formdata:
#         out += "#Duration,"
#
#     out += "\n"
#     for group in groups:
#
#         exam = Exams.getExamStruct(eid, group)
#         for uid in group["marks"].keys():
#
#             if "showid" in formdata:
#                 out += '%s,' % (Users.getStudentID(uid),)
#             if "showuname" in formdata:
#                 out += '%s,' % (Users.getUname(uid),)
#             if "showname" in formdata:
#                 out += '%s,%s,' % (Users.getFamilyName(uid), Users.getGivenName(uid))
#             mark = group["marks"][uid]['total']
#
#             if mark is None:
#                 mark = ""
#             if "showparts" in formdata:
#                 for qtid in exam['qtemplates']:
#                     try:
#                         part = group['marks'][uid]['Q%d' % (qtid,)]
#                         out += "%s," % (part,)
#                     except KeyError:
#                         out += ","
#             if "showmark" in formdata:
#                 out += '%s' % (mark,)
#             if "showduration" in formdata:
#                 out += ',%s' % (group["marks"][uid]['duration'],)
#             out += "\n"
#
#     return out
#

# This is taken from OaSetupFE, but should probably be moved into the database
# at some point.
def _getPermissionShort(pid):
    """ Return a short human readable name for the permission."""

    pNames = {1: "Super User",
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

    if pNames.has_key(pid):
        return pNames[pid]
    return None


def savePermissions(request, cid, user_id):
    """ Save permission changes
    """

    permlist = getCoursePerms(cid)
    perms = {}
    users = {}
    for perm in permlist:
        u = UserAPI.getUser(perm[0])
        uname = u['uname']
        if not uname in users:
            users[uname] = {}
        users[uname]['fullname'] = u['fullname']

        if not uname in perms:
            perms[uname] = []
        perms[uname].append(int(perm[1]))

    form = request.form
    if form:    # we received a form submission, so work out changes and save them
        fields = [field for field in form.keys() if field[:5] == "perm_"]
        newperms = {}

        for field in fields:
            uname = field.split('_')[1]
            perm = int(field.split('_')[2])

            if not uname in newperms:
                newperms[uname] = []
            newperms[uname].append(perm)

        for uname in users:
            uid = UserAPI.getUidByUname(uname)
            for perm in [2, 5, 10, 14, 11, 8, 9, 15]:
                if uname in newperms and perm in newperms[uname]:
                    if not perm in perms[uname]:
                        addPerm(uid, cid, perm)
                        audit(1,
                              user_id,
                              uid,
                              "CourseAdmin",
                              "%s given '%s' permission by %s" % (uname, _getPermissionShort(perm), user_id,)
                        )
                else:
                    if uname in perms and perm in perms[uname]:
                        deletePerm(uid, cid, perm)
                        audit(1,
                              user_id,
                              uid,
                              "CourseAdmin",
                              "%s had '%s' permission revoked by %s" % (uname, _getPermissionShort(perm), user_id,)
                        )

        for uname in newperms:
            uid = UserAPI.getUidByUname(uname)
            if not uname in perms:
                # We've added a user
                for perm in [2, 5, 10, 14, 11, 8, 9, 15]:
                    if perm in newperms[uname]:
                        addPerm(uid, cid, perm)
                        audit(1,
                              user_id,
                              uid,
                              "CourseAdmin",
                              "%s given '%s' permission by %s" % (uname, _getPermissionShort(perm), user_id,)
                        )
        if "adduser" in form:
            newuname = form['adduser']
            newuid = UserAPI.getUidByUname(newuname)
            if newuid:
                addPerm(newuid, cid, 10)
            audit(1,
                  user_id,
                  newuid,
                  "CourseAdmin",
                  "%s given '%s' permission by %s" % (newuname, _getPermissionShort(10), user_id,)
            )
    return


def ExamEditSubmit(request, user_id, cid, exam_id):
    """ Accept the submitted exam edit/create form.
        If exam_id is not provided, create a new one.
    """

    # TODO: More validation. Currently we trust the client validation, although the user is authenticated staff
    # so probably not too high a risk of shenanigans.

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
            dummy, q, p = k.split("_")
            if not q in qns:
                qns[q] = []
            qns[q].append(v[0])

    if not exam_id:
        exam_id = Exams.create(cid, user_id, title, atype, duration, astart, aend, instructions, code=code,
                               instant=instant)
    else:  # update
        Exams.setTitle(exam_id, title)
        Exams.setDuration(exam_id, duration)
        Exams.setType(exam_id, atype)
        Exams.setDescription(exam_id, instructions)
        Exams.setStart(exam_id, astart)
        Exams.setEnd(exam_id, aend)
        Exams.setCode(exam_id, code)
        Exams.setInstant(exam_id, instant)

    for pos, qts in qns.iteritems():
        OaDB.updateExamQTemplatesInPosition(exam_id, pos, qts)

    return exam_id

#
#
# def _getSubmitExam(session, course, student, exam):
#     """ Submit the assessment for the student (eg. when they didn't).
#     """
#
#     userid = session['user_id']
#     out = OaAssessFE.getAssessmentSubmitPage(student, course, exam)
#     audit(1, userid, student, "Assessment", "%s submitted exam %d for %s" % (Users.getUname(userid), exam, Users.getUname(student)))
#     return "Assessment submitted!. <a href='$SPATH$/courseadmin/examstatus/%d'>Return to marks page</a>%s" % (exam,out)
#
#
# def _getUnsubmitExam(session, course, student, exam):
#     """ Reset the exam timers and marks so the student can re-do or finish it.
#     """
#
#     userid = session['user_id']
#     Exams.unsubmit(exam, student)
#     audit(1, userid, student, "Assessment", "%s unsubmitted exam %d for %s" % (Users.getUname(userid), exam, Users.getUname(student)))
#     return "Assessment reset!. <a href='$SPATH$/courseadmin/examstatus/%d'>Return to marks page</a>" % (exam,)

#
# def _getPage(session, command, formdata, tmpl):
#     """Do the magic to fill in the main pane."""
#
#     out = ""
#     user_id = int(session['user_id'])
#     subcommands = command.split("/")
#
#     if not subcommands:
#         subcommands = [command, ""]
#
#     if subcommands[0]=='examstatus':
#         exam = int(subcommands[1])
#         course = Exams.getCourse(exam)
#         if (satisfyPerms(user_id, course,
#                 ("OASIS_VIEWMARKS", "OASIS_ALTERMARKS"))):
#             out = _getExamStatusPage(session, exam, tmpl)
#         else:
#             out = "You do not have access to administer this course."
#
#     if subcommands[0]=='unsubmit':
#         course = int(subcommands[1])
#         student = int(subcommands[2])
#         exam = int(subcommands[3])
#         if satisfyPerms(user_id, course, ("OASIS_ALTERMARKS",)):
#             return _getUnsubmitExam(session, course, student, exam)
#     elif subcommands[0]=='submit':
#         course = int(subcommands[1])
#         student = int(subcommands[2])
#         exam = int(subcommands[3])
#         if satisfyPerms(user_id, course, ("OASIS_ALTERMARKS",)):
#             return _getSubmitExam(session, course, student, exam)
#     return out


def _getSortedQuestionList(topic):
    def cmp_question_position(a, b):
        """Order questions by the absolute value of their positions
           since we use -'ve to indicate hidden.
        """

        return cmp(abs(a['position']), abs(b['position']))

    questionlist = OaGeneral.getQuestionListing(topic, None, False)

    if questionlist:
        # At the moment we use -'ve positions to indicate that a question is hidden
        # but when displaying them we want to maintain the sort order.
        for question in questionlist:
            # Usually questions with position 0 are broken or uninteresting so put them at the bottom.
            if question['position'] == 0:
                question['position'] = -10000
        questionlist.sort(cmp_question_position)
    else:
        questionlist = []

    return questionlist


def getCreateExamQuestionList(course):
    """ Return a list of questions that can be used to create an assessment
    """

    topics = Courses.getTopicsInfoAll(course, archived=0, numq=False)
    for num, topic in topics.iteritems():
        topic_id = topics[num]['id']
        topics[num]['questions'] = _getSortedQuestionList(topic_id)
    return topics

#
# def showMain(session, command="top", formdata=None):
#     """Page handler. Called by the dispatcher to handle the setup
#        section."""
#
#
#
#     # WARNING: Remember to check arguments carefully to stop people putting scripting in URLs
#     # Casting them to int is generally a good plan
#     subcommands = command.split("/")
#     cmd = subcommands[0]
#     user_id = session['user_id']
#
#
#
#     if subcommands[0]=='exammarks':
#         exam = int(subcommands[2])
#         course_id = Exams.getCourse(exam)
#         course_info = CourseAPI.getCourse(course_id)
#         now = datetime.datetime.now()
#         OaSession.showHTTPHeader(session, contenttype = "text/csv", disposition = 'inline; filename="%s-results-%s-%s.csv"' % (course_info['name'], Exams.getTitle(exam), OaGeneralBE.humanDate(now)))
#         if (satisfyPerms(user_id, course_id,
#                 ("OASIS_VIEWMARKS", "OASIS_ALTERMARKS"))):
#             out = _getExamsMarksDownload(course_id, exam, formdata)
#         else:
#             out = "You do not have access to administer this course."
#         OaSession.showHTML(session, out)
#         return True
#
#     loader = TemplateLoader([OaConfig.homedir + "/html", ], variable_lookup='lenient')
#
#     tmpl = loader.load("page-std.xhtml")
#     try:
#         page = _getPage(session, command, formdata, tmpl)
#         OaSession.showHTTPHeader(session, contenttype = "text/html; charset=UTF-8", disposition = None)
#         OaSession.showHTML(session, page)
#     except sendRedirect, e:
#         OaSession.sendRedirect(session, e.target)
#
#     return True
