# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" OaSetup.py
    Setup related stuff.
"""

from flask import flash
from logging import log, ERROR
from oasis.lib import DB, Topics, Courses, Courses2


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
        DB.update_qt_title(qid, title)

    # Then positions
    for command in [cmd for cmd in cmdlist if cmd['cmd'] == 'position']:
        qtid = int(command['data'])
        try:
            position = int(command['value'])
        except ValueError:
            position = 0
        DB.update_qt_pos(qtid, topic_id, position)

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
                    qt_title = DB.get_qt_name(qtid)
                    topic_title = Topics.get_name(topic_id)
                    flash("Moving %s to %s" % (qt_title, topic_title))
                    DB.move_qt_to_topic(qtid, target_topic)
        if target_cmd == 'copy':
            if target_topic:
                for qtid in qtids:
                    qt_title = DB.get_qt_name(qtid)
                    topic_title = Topics.get_name(topic_id)
                    flash("Copying %s to %s" % (qt_title, topic_title))
                    newid = DB.copy_qt_all(qtid)
                    DB.add_qt_to_topic(newid, target_topic)

        if target_cmd == 'hide':
            for qtid in qtids:
                position = DB.get_qtemplate_topic_pos(qtid, topic_id)
                if position > 0:  # If visible, make it hidden
                    DB.update_qt_pos(qtid, topic_id, -position)
                    title = DB.get_qt_name(qtid)
                    flash("Made '%s' Hidden" % title)

        if target_cmd == 'show':
            for qtid in qtids:
                position = DB.get_qtemplate_topic_pos(qtid, topic_id)
                if position == 0:  # If hidden, make it visible
                    newpos = DB.getMaxQTemplatePositionInTopic(topic_id)
                    DB.update_qt_pos(qtid, topic_id, newpos + 1)
                    title = DB.get_qt_name(qtid)
                    flash("Made '%s' Visible" % title)
                if position < 0:  # If hidden, make it visible
                    DB.update_qt_pos(qtid, topic_id, -position)
                    title = DB.get_qt_name(qtid)
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
            newid = DB.create_qt(user_id, new_title, "No Description", 1, new_maxscore, 0)
            if newid:
                mesg.append("Created new question, id %s" % newid)
                DB.update_qt_pos(newid, topic_id, new_position)
                DB.create_qt_att(newid, "qtemplate.html", "application/oasis-html", "empty", 1)
                DB.create_qt_att(newid, "qtemplate.html", "application/oasis-html", "empty", 1)
                if new_qtype == "oqe":
                    mesg.append("Creating new question, id %s as OQE" % newid)
                    DB.create_qt_att(newid, "_editor.oqe", "application/oasis-oqe", "", 1)
                if new_qtype == "raw":
                    mesg.append("Creating new question, id %s as RAW (%s)" % (newid, new_qtype))
                    DB.create_qt_att(newid, "datfile.txt", "application/oasis-dat", "0", 1)
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


def get_sorted_courselist(with_stats=False, only_active=True):
    """Return a list of courses suitable for choosing one to edit
         [  ('example101', { coursedict }),  ('sorted302', { coursedict } )  ]
    """

    courses = Courses2.getCourseDict(only_active = only_active)

    inorder = []
    for cid, course in courses.iteritems():
        if with_stats:
            course['students'] = Courses.get_users(cid)
            course['size'] = len(course['students'])
        inorder.append((course['name'], course))
    inorder.sort()
    return inorder
