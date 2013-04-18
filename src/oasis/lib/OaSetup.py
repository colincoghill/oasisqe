# -*- coding: utf-8 -*-

""" OaSetup.py
    Setup related stuff.
"""

from flask import flash

from logging import log, ERROR

#
#
# def _doViewExam(student, exam):
#     """ Return the HTML for a page showing the students instance of the exam, with
#         their answers, and a marking summary.
#     """
#
#     assert(int(exam))
#     examtitle = Exams.getTitle(exam)
#     examsubmit = Exams.getSubmitTime(exam, student)
#     course_id = Exams.getCourse(exam)
#     course_info = CourseAPI.getCourse(course_id)
#     course_title = course_info['name']
#     username = Users.getUname(student)
#     fname = Users.getFullName(student)
#     questions = OaGeneralBE.getExamQuestions(student, exam)
#
#     firstview = None
#     lastmark = None
#
#     out = "<h2>%s</h2>\n" % (course_title,)
#     out += "<h3>%s</h3>\n" % (examtitle,)
#     out += "<h3>%s (%s)</h3>\n" % (fname, username)
#     out += "<h3>Submitted: %s</h3>" % (examsubmit,)
#     if examsubmit:
#         out += "<form method='post' action='$SPATH$/courseadmin/unsubmit/%d/%d/%d'><input type='submit' name='Un-Submit' value='unsubmit' /></form> - reset timer and allow student to re-do the assessment\n" % (course_id, student, exam)
#     else:
#         out += "<form method='post' action='$SPATH$/courseadmin/submit/%d/%d/%d'><input type='submit' name='Submit' value='submit' /></form> for marking.\n" % (course_id, student, exam)
#
#     for question in questions:
#         qtemplate = OaDB.getQuestionParent(question)
#
#         questionmark = OaDB.getQuestionMarkTime(question)
#         questionview = OaDB.getQuestionViewTime(question)
#
#         answers = OaDB.getQuestionGuessesBeforeTime(question, examsubmit)
#
#         # we're working out the first time the assessment was viewed is the
#         # earliest time a question in it was viewed, and the time the assessment
#         # was marked is the last marking time of a question in it.
#         # (We're trying to work out how long they took to do the assessment)
#         if firstview:
#             if questionview < firstview:
#                 firstview = questionview
#         else:
#             firstview = questionview
#
#         if lastmark:
#             if questionmark > lastmark:
#                 lastmark = questionmark
#         else:
#             lastmark = questionmark
#
#         out += "<hr><H2>Question %d</H2>" % (OaDB.getQTemplatePositionInExam(exam, qtemplate))
#         marks = OaGeneralBE.markQuestion(question, answers)
#         out += "<form method='post' action='$SPATH$/setup/viewpastexam/%s/%s'><table class='questionlist'>" % (student, exam)
#         out += "<tr class='questionlist'>"
#         out += "<th class='questionlist'>Part</th>"
#         out += "<th class='questionlist'>Guess</th>"
#         out += "<th class='questionlist'>Answer</th>"
#         out += "<th class='questionlist'>Tolerance</th>"
#         out += "<th class='questionlist'>Score</th>"
#         out += "<th class='questionlist'>Comment</th></tr>\n"
#         parts = [int(var[1:]) for var in marks.keys() if re.search("^A([0-9]+$)", var) > 0]
#         parts.sort()
#         for part in parts:
#             guess = marks['G%d' % (part,)]
#             answer = marks['A%d' % (part,)]
#             score = marks['M%d' % (part,)]
#             tolerance = marks['T%d' % (part,)]
#             comment = marks['C%d' % (part,)]
#             out += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s%%</td><td>%s</td><td>%s</td></tr>" % (
#                     part, guess, answer, tolerance, score, comment)
#             out += "<input type='hidden' name='question_id' value='%d' />" % (question,)
#         out += "</table></form>"
#
#         out += OaGeneralBE.renderQuestionHTML(question)
#
#     return out
from oasis.lib import OaDB, Topics, Courses, CourseAPI


def doTopicPageCommands(request, topic_id, user_id):
    """We've been asked to perform some operations on the Topic page.

        Expecting form fields:

            selected_QTID
            position_QTID
            name_QTID

        where QTID is a question template id. May receive many.

            new_position
            new_name
            new_type

            select_cmd = 'copy' | 'move'
            select_target = TOPICID of target topic

    """

    form = request.form
    mesg = []

    # Make a list of all the commands to run
    cmdlist = []
    for command in request.form.keys():
        (cmd, data) = command.split('_', 2)
        value = form[command]
        if not value == "none":
            cmdlist += [{'cmd': cmd, 'data': data, 'value': value}]

    # Now run them:
    # Titles first
    for command in [cmd for cmd in cmdlist if cmd['cmd'] == 'name']:
        qid = int(command['data'])
        title = command['value']
        OaDB.updateQTemplateTitle(qid, title)

    # Then positions
    for command in [cmd for cmd in cmdlist if cmd['cmd'] == 'position']:
        qtid = int(command['data'])
        try:
            position = int(command['value'])
        except ValueError:
            position = 0
        OaDB.updateQTemplatePosition(qtid, topic_id, position)

    # Then commands on selected questions
    target_cmd = form.get('target_cmd', None)
    if target_cmd:
        qtids = [int(cmd['data']) for cmd in cmdlist if cmd['cmd'] == 'select']
        try:
            target_topic = int(form.get('target_topic', 0))
        except ValueError:
            target_topic = None

        if target_cmd == 'move':
            if target_topic:
                for qtid in qtids:
                    qt_title = OaDB.getQTemplateName(qtid)
                    topic_title = Topics.getName(topic_id)
                    flash("Moving %s to %s" % (qt_title, topic_title))
                    OaDB.moveQTemplateToTopic(qtid, target_topic)
        if target_cmd == 'copy':
            if target_topic:
                for qtid in qtids:
                    qt_title = OaDB.getQTemplateName(qtid)
                    topic_title = Topics.getName(topic_id)
                    flash("Copying %s to %s" % (qt_title, topic_title))
                    newid = OaDB.copyQTemplateAll(qtid)
                    OaDB.addQTemplateToTopic(newid, target_topic)

        if target_cmd == 'hide':
            for qtid in qtids:
                position = OaDB.getQTemplatePositionInTopic(qtid, topic_id)
                if position > 0:  # If visible, make it hidden
                    OaDB.updateQTemplatePosition(qtid, topic_id, -position)
                    title = OaDB.getQTemplateName(qtid)
                    flash("Made '%s' Hidden" % title)

        if target_cmd == 'show':
            for qtid in qtids:
                position = OaDB.getQTemplatePositionInTopic(qtid, topic_id)
                if position == 0:  # If hidden, make it visible
                    newpos = OaDB.getMaxQTemplatePositionInTopic(topic_id)
                    OaDB.updateQTemplatePosition(qtid, topic_id, newpos + 1)
                    title = OaDB.getQTemplateName(qtid)
                    flash("Made '%s' Visible" % title)
                if position < 0:  # If hidden, make it visible
                    OaDB.updateQTemplatePosition(qtid, topic_id, -position)
                    title = OaDB.getQTemplateName(qtid)
                    flash("Made '%s' Visible" % title)

    # Then new questions
    new_title = form.get('new_title', None)
    if new_title:
        if not (new_title == "[New Question]" or new_title == ""):
            new_position = form.get('new_position', 0)
            try:
                new_position = int(new_position)
            except ValueError:
                new_position = 0
            new_qtype = form.get('new_qtype', 'raw')
            try:
                new_maxscore = float(form.get('new_maxscore', 0))
            except ValueError:
                new_maxscore = 0
            newid = OaDB.createQTemplate(user_id, new_title, "No Description", 1, new_maxscore, 0)
            if newid:
                mesg.append("Created new question, id %s" % newid)
                OaDB.updateQTemplatePosition(newid, topic_id, new_position)
                OaDB.createQTAttachment(newid, "qtemplate.html", "application/oasis-html", "empty", 1)
                OaDB.createQTAttachment(newid, "qtemplate.html", "application/oasis-html", "empty", 1)
                if new_qtype == "oqe":
                    mesg.append("Creating new question, id %s as OQE" % newid)
                    OaDB.createQTAttachment(newid, "_editor.oqe", "application/oasis-oqe", "", 1)
                if new_qtype == "raw":
                    mesg.append("Creating new question, id %s as RAW (%s)" % (newid, new_qtype))
                    OaDB.createQTAttachment(newid, "datfile.txt", "application/oasis-dat", "0", 1)
            else:
                mesg.append("Error creating new question, id %s" % newid)
                log(ERROR, "Unable to create new question (%s) (%s)" % (new_title, new_position))
    return {'mesg': mesg}

#
#
# def _processClassListUpload(session, course_id, formdata):
#     """ Accept an uploaded CSV file and update the list of students in the course from it.
#     """
#
#     data = formdata['newlist'].value
#     data = data.replace('"', '')
#     data = data.split("\n")
#
#     course_info = CourseAPI.getCourse(course_id)
#     classname = course_info['name']
#
#     # assume we're using the group of the same name as the course
#     oasis_groupid = Groups.getGroupByTitle(classname)
#     out = "<h3>Processing New Class List</h3>"
#     out += "<br />Return to <a href='$SPATH$/courseadmin/top/%d'>Course Page</a>" % course_id
#
#     if not oasis_groupid:
#         out += "Course %s isn't in OASIS." % (classname,)
#         return out
#
#     import_userlist = []
#     for line in data:
#         if "\t" in line:
#             e = line.split("\t")
#         else:
#             e = line.split(",")
#         if len(e) >= 4:
#             import_userlist.append({'oasis_id': None,
#                                     'netid': e[0].rstrip().lstrip(),
#                                     'family_name': e[1].rstrip().lstrip(),
#                                     'given_name': e[2].rstrip().lstrip(),
#                                     'universityid': e[3].rstrip()})
#         else:
#             if len(line) > 4:
#                 out += "<li>Bad line: <pre>%s</pre></li>" % line
#
#     for k in import_userlist:
#         k['oasis_id'] = Users.getUidByUname(k['netid'])
#
#     Groups.flushUsersInGroup(oasis_groupid)
#     for i in import_userlist:
#         if i['oasis_id'] is not None:
#             if oasis_groupid is not None:
#                 out += "<li>adding %s to %s</li>" % (i['netid'], classname)
#                 Groups.addUserToGroup(i['oasis_id'], oasis_groupid)
#         else:
#             Users.create(i['netid'], "secret", i['given_name'], i['family_name'], 3, i['universityid'])
#             out += "<li style='color: green;'>create account for %s (%s)</li>" % (i['netid'], i['universityid'])
#             uid = Users.getUidByUname(i['netid'])
#             if not uid:
#                 out += "<li style='color: red;'>Unable to create user account for %s</li>" % (i,)
#             else:
#                 if oasis_groupid is not None:
#                     out += "<li style='color: green;'>Adding %s to %s</li>" % (i['netid'], classname)
#                     Groups.addUserToGroup(i['oasis_id'], oasis_groupid)
#                 out += "<li style='color: green;'>Password for %s Set to [%s]</li>" % (i['netid'], i['universityid'])
#                 Audit.audit(1, session['user_id'], uid,
#                             "UserImport", "%s reset password for %s." % (
#                             session['username'], i['netid']))
#                 Users.setPassword(uid, i['universityid'])
#
#     out += "<p>%d students in course</p>" % (len(import_userlist))
#     out += "<br />Return to <a href='$SPATH$/setup/coursequestions/%d'>Course Page</a>" % (course_id,)
#
#     return out
#
#
# def _getClassListUpload(session, course, formdata):
#     """ Allow the user to upload a CSV file containing the list of
#         students in the given course.
#     """
#
#     out = "ERROR"
#     if "submit" in formdata:
#         if "newlist" in formdata:
#             output = _processClassListUpload(session, course, formdata)
#             return output
#
#     else:
#         course_info = CourseAPI.getCourse(course)
#         coursetitle = course_info['name']
#
#         out = "<h2>Upload New Classlist</h2>"
#         out += "<p>Please choose a .csv file containing the list of students in %s.</p>" % coursetitle
#         out += "<p><i>The first 4 columns of the file should be: <br />"
#         out += "<pre>netid,familyname,givenname,studentid</pre></i></p>"
#         out += "<p>For example:</p><pre>jblo934,Bloggs,Joe,12345678</pre>"
#         out += "<form method='post' ENCTYPE='multipart/form-data' >"
#         out += "<input type='file' name='newlist' />"
#         out += "<input type='submit' name='submit' value='Upload' />"
#         out += "</form>"
#         out += "<br />Return to <a href='$SPATH$/courseadmin/top/%d'>Course Page</a>" % course
#     return out
#
#
# def _getPersonalPage(session, formdata):
#     """ A 'personal page' which allows the user to control various settings and view some
#         statistics about themselves.
#     """
#
#     user_id = session['user_id']
#     message = ""
#
#     if formdata.has_key("ChangePassword"):
#         if not formdata.has_key("password1"):
#             message += "<H3>You need to enter a new password.</H3>"
#         else:
#             newpass = formdata['password1'].value
#             if not formdata.has_key("password2"):
#                 message += "<H3>You need to enter a confirmation password.</H3>"
#             else:
#                 confirmpass = formdata['password2'].value
#                 if not newpass == confirmpass:
#                     message += "<H3>Passwords don't match</H3>"
#                 else:
#                     Users.setPassword(user_id, newpass)
#                     Audit.audit(1, session['user_id'], user_id, "UserAuth", "%s reset password for %s." % (Users.getUname(user_id), Users.getUname(user_id)))
#                     message += "<H3>Password Changed!</H3>"
#
#     out = "<FORM METHOD='post' ACTION='$SPATH$/setup/personal'>"
#     out += OaSession.getPersonalityFile("html/personalpage.html")
#     out = out.replace("$GIVENNAME$", Users.getGivenName(user_id))
#     out = out.replace("$FAMILYNAME$", Users.getFamilyName(user_id))
#     out = out.replace("$LOGINNAME$", Users.getUname(user_id))
#     out = out.replace("$PASSWORD$", "")
#     out = out.replace("$MESSAGE$", message)
#     out += "</FORM>"
#
#     return out
#
#
# def _getOtherPersonalPage(session, subcommands, formdata):
#     """ A 'personal page' which allows the user to control various settings and view some
#         statistics about other users.
#     """
#
# #    user_id = session['user_id']
#     user_id = int(subcommands[0])
#     message = ""
#
#     if formdata.has_key("ChangePassword"):
#         if not formdata.has_key("password1"):
#             message += "<H3>You need to enter a new password.</H3>"
#         else:
#             newpass = formdata['password1'].value
#             if "password2" in formdata:
#                 message += "<H3>You need to enter a confirmation password.</H3>"
#             else:
#                 confirmpass = formdata['password2'].value
#                 if not newpass == confirmpass:
#                     message += "<H3>Passwords don't match</H3>"
#                 else:
#                     Users.setPassword(user_id, newpass)
#                     Audit.audit(1,
#                                 session['user_id'],
#                                 user_id,
#                                 "UserAuth",
#                                 "%s reset password for %s." % (Users.getUname(session['user_id']), Users.getUname(user_id)))
#                     message += "<H3>Password Changed!</H3>"
#
#     out = "<FORM METHOD='post' ACTION='$SPATH$/setup/passwd/%d'>" % user_id
#     out += OaSession.getPersonalityFile("html/personalpage.html")
#     out = out.replace("$GIVENNAME$", Users.getGivenName(user_id))
#     out = out.replace("$FAMILYNAME$", Users.getFamilyName(user_id))
#     out = out.replace("$LOGINNAME$", Users.getUname(user_id))
#     out = out.replace("$PASSWORD$", "")
#     out = out.replace("$MESSAGE$", message)
#     out += "</FORM>"
#
#     return out
#
#
# def _showStudentSearchPage(course, formdata):
#     """ Present a page allowing the user to search for user accounts to view history.
#     """
#
#     if course:
#         course_info = CourseAPI.getCourse(course)
#         course_title = course_info['name']
#     else:
#         course_title = ""
#     findname = ''
#
#     if formdata.has_key("usersearch_name"):
#         findname = formdata['usersearch_name'].value
#
#     out = "<H2>Student Records</H2>"
#     out += "<H3>%s</H3>" % (course_title,)
#     out += "<FORM METHOD='post' ACTION='$SPATH$/setup/studentsearch/%s'>" % (course,)
#     out += "Search for: <INPUT TYPE='text' NAME='usersearch_name' VALUE='%s' >" % (findname,)
#     out += "</FORM>"
#
#     matches = None
#
#     if findname == '' or findname is None:
#         out += "<H3>Class List:</H3>"
#         matches = Courses.getUsersInCourse(course)
#
#     if not findname == '':
#         out += "<H3>Search results:</H3>"
#         matches = Users.find(findname)
#
#     if matches:
#         out += "<table>"
#         for userid in matches:
#             out += "<tr><th><a href='$SPATH$/setup/studentview/%d/%d'>%s</a></th><td>%s</td><td>%s</td></tr>" % (
#                    userid, course, Users.getUname(userid), Users.getFullName(userid), Users.getStudentID(userid))
#         out += "</table>"
#
#     return out


def getSortedCourseList(with_stats=False, only_active=True):
    """Return a list of courses suitable for choosing one to edit
         [  ('example101', { coursedict }),  ('sorted302', { coursedict } )  ]
    """

    courses = CourseAPI.getCourseDict(only_active = only_active)

    inorder = []
    for cid, course in courses.iteritems():
        if with_stats:
            course['students'] = Courses.getUsersInCourse(cid)
            course['size'] = len(course['students'])
        inorder.append((course['name'], course))
    inorder.sort()
    return inorder

#
#
# def _getPane(session, command, formdata):
#     """ Do the magic to fill in the main pane.
#     """
#
#     out = ""
#     user_id = session['user_id']
#     subcommands = command.split("/")
#
#     if not subcommands:
#         subcommands = [command, ""]
#
#     # Complex stuff. Needs some smarts:
#     if subcommands[0] == 'personal':
#         return _getPersonalPage(session, formdata)
#     if subcommands[0] == 'passwd':
#         if not checkPermission(session['user_id'], -1, "OASIS_USERADMIN"):
#             return "You do not have enough access to access user records."
#         return _getOtherPersonalPage(session, subcommands[1:], formdata)
#     if subcommands[0] == 'uploadclass':
#         if len(subcommands) >= 2 :
#             course = int(subcommands[1])
#         else:
#             course = None
#         if not checkPermission(session['user_id'], course, "OASIS_USERADMIN"):
#             return "You do not have enough access to access user records."
#         return _getClassListUpload(session, course, formdata)
#     if subcommands[0] == 'studentsearch':
#         if len(subcommands) >= 2:
#             course = int(subcommands[1])
#         else:
#             course = None
#         if not checkPermission(session['user_id'], -1, "OASIS_VIEWMARKS"):
#             return "You do not have enough access to access user records."
#         return _showStudentSearchPage(course, formdata)
#     if subcommands[0] == 'viewexam':
#         course = int(subcommands[1])
#         student = int(subcommands[2])
#         exam = int(subcommands[3])
#         if satisfyPerms(user_id, course, ("OASIS_VIEWMARKS", )):
#             return _doViewExam(student, exam)
#         else:
#             return "You do not have 'View Marks' permission on this course."
#
#     return out
#
#
# def showMain(session, command="top", formdata=None):
#     """ Page handler. Called by the dispatcher to handle the practice
#         section.
#     """
#     # WARNING: Remember to check arguments carefully to stop people putting scripting in URLs
#     # Casting them to int is generally a good plan
#
#     user_id = session['user_id']
#     subcommands = command.split("/")
#     cmd = subcommands[0]
#
#     if cmd == 'viewexam':
#         course = int(subcommands[1])
#         if len(subcommands) >= 5:
#             qid = int(subcommands[3])
#             attach = subcommands[4]
#         else:
#             qid = None
#             attach = None
#         if satisfyPerms(user_id, course, ("OASIS_VIEWMARKS", )):
#             if qid and attach:
#                 log("info",
#                     "OaSetupFE::commands",
#                     "Show attachment %s" % (attach,))
#                 showAttachment(session, qid, attach)
#                 return
#
#     return 1
