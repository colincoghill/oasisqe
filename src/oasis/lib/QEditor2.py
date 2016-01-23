# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

"""Provides a question editing interface to the user. The question can be
   created by assembling "blocks" of different types. Eg. text, picture, answer.
"""

# WANTED: a better name than "QE2"


from oasis.lib import DB
from oasis.lib import Audit
from logging import getLogger
import re
import json


L = getLogger("oasisqe")


def create_new(qt_id, name):
    """
    Set the given qtemplate up as a new (default) question. Makes sure
    the appropriate things the editor needs are configured and in place.
    Assumes the QT has not previously been set up.

    :param qt_id: The ID of the qtemplate to set up.
    :param name: Name of the question.
    :return:
    """

    # The _editor.qe2 file contains a json object with most of the structural
    # information about the question.
    default_ = {
        'name': name,
        'qe_version': 0.1
    }
    DB.create_qt_att(qt_id,
                     "__editor.qe2",
                     "application/oasis-qe2",
                     json.dumps(default_),
                     1)
    return


def process_save(qt_id, topic_id, request, session, version):
    """ Have received a web form POST to save the current changes.

    :param qt_id: ID of the question template being edited
    :param topic_id: Topic the question template is in
    :param request: The POST request.
    :param session: The web session object
    :param version: (int) the new version of the qt being saved
    :return: None
    """

    form = request.form
    files = request.files

    if 'blocks' in form:
        blocks = form['blocks'].encode("utf8")
        DB.create_qt_att(qt_id,
                         "__editor.qe2",
                         "text/json",
                         blocks,
                         version)
    else:
        raise KeyError("blocks")

    return


def qtlog_as_html(topic, qtid):
    """Show the most recent log errors for the given qtid.
    """
    versionre = re.compile(r'version=(\d+),')
    variationre = re.compile(r'variation=(\d+),')
    priorityre = re.compile(r'priority=([^,]+),')
    facilityre = re.compile(r'facility=([^,]+),')
    messagere = re.compile(r'message=(.+)$', re.MULTILINE)

    out = ""
    name = DB.get_qt_name(qtid)
    out += "<h2>Log Entries for %s, topic %s</h2>" % (name, topic)
    out += "<p><i>These can be created from within __marker.py or __results.py by calling "
    out += "log(priority, mesg), for example:</i> "
    out += "<pre>log('error','User entered a value we can't parse.')</pre></p>"
    out += "<p><i>Typical priorities might be 'error', 'info', 'noise'</i></p>"
    out += "<table style='border: solid 1px black;' border='1'><tr><th>Time</th><th>Ver</th>"
    out += "<th>Variation</th><th>Pri</th><th>Fac</th><th>Message</th></tr>"
    entries = Audit.get_records_by_object(qtid, limit=100, offset=0)
    for entry in entries:
        try:
            version = versionre.findall(entry['message'])[0]
        except (IndexError, TypeError):
            version = '.'
        try:
            variation = variationre.findall(entry['message'])[0]
        except (IndexError, TypeError):
            variation = '.'
        try:
            priority = priorityre.findall(entry['message'])[0]
        except (IndexError, TypeError):
            priority = '.'
        try:
            facility = facilityre.findall(entry['message'])[0]
        except (IndexError, TypeError):
            facility = '.'
        try:
            message = messagere.findall(entry['message'])[0]
        except (IndexError, TypeError):
            message = '.'
        out += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (entry['time'].strftime("%Y/%b/%d %H:%M:%S"), version, variation, priority, facility, message)
    out += "</table>"
    return out
