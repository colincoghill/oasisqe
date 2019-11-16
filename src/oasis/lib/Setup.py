# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" OaSetup.py
    Setup related stuff.
"""

from flask import flash
from oasis.lib import DB, Topics, Courses
import io
from oasis.lib import External
from flask import send_file, abort
from logging import getLogger
from oasis.lib import QEditor, QEditor2

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
    files = request.files

    mesg = []

    # Make a list of all the commands to run
    cmdlist = []
    for command in list(request.form.keys()):
        if '_' in command:
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
        DB.update_qt_practice_pos(qtid, position)

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
                    Topics.flush_num_qs(target_topic)
        if target_cmd == 'copy':
            if target_topic:
                for qtid in qtids:
                    qt_title = DB.get_qt_name(qtid)
                    topic_title = Topics.get_name(target_topic)
                    flash("Copying %s to %s" % (qt_title, topic_title))
                    position = DB.get_qtemplate_practice_pos(qtid)
                    newid = DB.copy_qt_all(qtid)
                    DB.move_qt_to_topic(newid, target_topic, position)
                    Topics.flush_num_qs(target_topic)

        if target_cmd == 'hide':
            for qtid in qtids:
                position = DB.get_qtemplate_practice_pos(qtid)
                if position > 0:  # If visible, make it hidden
                    DB.update_qt_practice_pos(qtid, -position)
                    title = DB.get_qt_name(qtid)
                    flash("Made '%s' Hidden" % title)

        if target_cmd == 'show':
            for qtid in qtids:
                position = DB.get_qtemplate_practice_pos(qtid)
                if position == 0:  # If hidden, make it visible
                    newpos = DB.get_qt_max_pos_in_topic(topic_id)
                    DB.update_qt_practice_pos(qtid, newpos + 1)
                    title = DB.get_qt_name(qtid)
                    flash("Made '%s' Visible" % title)
                if position < 0:  # If hidden, make it visible
                    DB.update_qt_practice_pos(qtid, -position)
                    title = DB.get_qt_name(qtid)
                    flash("Made '%s' Visible" % title)
        if target_cmd == "export":
            if len(qtids) < 1:
                flash("No questions selected to export")
            else:
                data = External.qts_to_zip(qtids)
                if not data:
                    abort(401)

                sio = io.StringIO(data)
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
            new_id = DB.create_qt(owner=user_id,
                                  title=new_title,
                                  desc="No Description",
                                  marker=1,
                                  score_max=new_max_score,
                                  status=0,
                                  topic_id=topic_id)
            if new_id:
                mesg.append("Created new question, id %s" % new_id)
                if new_position and new_position >= 1:
                    DB.update_qt_practice_pos(new_id, new_position)

                if new_qtype == "qe2":
                    mesg.append("Creating new question, id %s as QE2" % new_id)
                    QEditor2.create_new(new_id, new_title)

                if new_qtype == "raw":
                    mesg.append("Creating new question, id %s as RAW (%s)" %
                                (new_id, new_qtype))
                    QEditor.create_new(new_id, new_title)

            else:
                mesg.append("Error creating new question, id %s" % new_id)
                L.error("Unable to create new question (%s) (%s)" %
                        (new_title, new_position))

    L.info("request.files = %s" % (repr(list(request.files.keys()))))
    # Did they upload a file to import?
    if 'import_file' in request.files:
        L.info("File upload to topic %s by user %s" % (topic_id, user_id))
        data = files['import_file'].read()
        if len(data) > 1:
            for msg in _import_questions_from_file(data, topic_id):
                mesg.append(msg)

    Topics.flush_num_qs(topic_id)

    return 1, {'mesg': mesg}


def _import_questions_from_file(data, topic_id):
    """ Take a data string with a question export and import questions from it into the given topic.
        :returns [string,]: list of (string) messages
    """
    mesg = []
    if len(data) > 52000000:  # approx 50Mb
        mesg.append("Upload is too large, 50MB Maximum.")

    num = External.import_qts_from_zip(data, topic_id=topic_id)
    if num is False:
        mesg.append("Invalid OASISQE file? No data recognized.")
    if num is 0:
        mesg.append("Empty OASISQE file? No questions found.")

    mesg.append("%s questions imported!" % num)
    return mesg


def get_sorted_courselist(with_stats=False, only_active=True):
    """Return a list of courses suitable for choosing one to edit
         [  ('example101', { coursedict }),  ('sorted302', { coursedict } )  ]
    """

    courses = Courses.get_courses_dict(only_active=only_active)

    inorder = []
    for cid, course in courses.items():
        if with_stats:
            course['students'] = Courses.get_users(cid)
            course['size'] = len(course['students'])
        inorder.append((course['name'], course))
    inorder.sort()
    return inorder
