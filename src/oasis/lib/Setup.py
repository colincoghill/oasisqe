# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" OaSetup.py
    Setup related stuff.
"""

from flask import flash
from oasis.lib import DB, Topics, Courses, Courses2
import StringIO
from oasis.lib import External
from flask import send_file, abort
from logging import getLogger

L = getLogger("oasisqe")


def do_topic_page_commands(request, topic_id, user_id):
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
                    topic_title = Topics.get_name(target_topic)
                    flash("Moving %s to %s" % (qt_title, topic_title))
                    DB.move_qt_to_topic(qtid, target_topic)
                    Topics.flush_num_qs(topic_id)
                    Topics.flush_num_qs(target_topic)
        if target_cmd == 'copy':
            if target_topic:
                for qtid in qtids:
                    qt_title = DB.get_qt_name(qtid)
                    topic_title = Topics.get_name(target_topic)
                    flash("Copying %s to %s" % (qt_title, topic_title))
                    newid = DB.copy_qt_all(qtid)
                    DB.add_qt_to_topic(newid, target_topic)
                    Topics.flush_num_qs(target_topic)

        if target_cmd == 'hide':
            for qtid in qtids:
                position = DB.get_qtemplate_topic_pos(qtid, topic_id)
                if position > 0:  # If visible, make it hidden
                    DB.update_qt_pos(qtid, topic_id, -position)
                    title = DB.get_qt_name(qtid)
                    flash("Made '%s' Hidden" % title)
                    Topics.flush_num_qs(topic_id)

        if target_cmd == 'show':
            for qtid in qtids:
                position = DB.get_qtemplate_topic_pos(qtid, topic_id)
                if position == 0:  # If hidden, make it visible
                    newpos = DB.get_qt_max_pos_in_topic(topic_id)
                    DB.update_qt_pos(qtid, topic_id, newpos + 1)
                    Topics.flush_num_qs(topic_id)
                    title = DB.get_qt_name(qtid)
                    flash("Made '%s' Visible" % title)
                if position < 0:  # If hidden, make it visible
                    DB.update_qt_pos(qtid, topic_id, -position)
                    Topics.flush_num_qs(topic_id)
                    title = DB.get_qt_name(qtid)
                    flash("Made '%s' Visible" % title)
        if target_cmd == "export":
            if len(qtids) < 1:
                flash("No questions selected to export")
            else:
                data = External.qts_to_zip(qtids)
                if not data:
                    abort(401)

                sio = StringIO.StringIO(data)
                return 2, send_file(sio, "application/oasisqe", as_attachment=True, attachment_filename="oa_export.zip")

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
                new_max_score = float(form.get('new_maxscore', 0))
            except ValueError:
                new_max_score = 0
            newid = DB.create_qt(user_id,
                                 new_title,
                                 "No Description",
                                 1,
                                 new_max_score,
                                 0)
            if newid:
                mesg.append("Created new question, id %s" % newid)
                DB.update_qt_pos(newid,
                                 topic_id,
                                 new_position)
                DB.create_qt_att(newid,
                                 "qtemplate.html",
                                 "application/oasis-html",
                                 "empty",
                                 1)
                DB.create_qt_att(newid,
                                 "qtemplate.html",
                                 "application/oasis-html",
                                 "empty",
                                 1)
                if new_qtype == "oqe":
                    mesg.append("Creating new question, id %s as OQE" % newid)
                    DB.create_qt_att(newid,
                                     "_editor.oqe",
                                     "application/oasis-oqe",
                                     "",
                                     1)
                if new_qtype == "raw":
                    mesg.append("Creating new question, id %s as RAW (%s)" %
                                (newid, new_qtype))
                    DB.create_qt_att(newid,
                                     "datfile.txt",
                                     "application/oasis-dat",
                                     "0",
                                     1)
            else:
                mesg.append("Error creating new question, id %s" % newid)
                L.error("Unable to create new question (%s) (%s)" %
                    (new_title, new_position))
    Topics.flush_num_qs(topic_id)

    return 1, {'mesg': mesg}


def get_sorted_courselist(with_stats=False, only_active=True):
    """Return a list of courses suitable for choosing one to edit
         [  ('example101', { coursedict }),  ('sorted302', { coursedict } )  ]
    """

    courses = Courses2.get_course_dict(only_active=only_active)

    inorder = []
    for cid, course in courses.iteritems():
        if with_stats:
            course['students'] = Courses.get_users(cid)
            course['size'] = len(course['students'])
        inorder.append((course['name'], course))
    inorder.sort()
    return inorder
