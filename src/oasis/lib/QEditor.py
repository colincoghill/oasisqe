# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

"""Provides a "raw" question editing interface to the user. Allows the user
   to create all the low level attachments and scripts used by OASIS questions
   directly."""

from oasis.lib import DB
from oasis.lib import Audit
from logging import getLogger
import re

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

    # Raw questions require the user to provide qtemplate.html
    DB.create_qt_att(new_id,
                     "qtemplate.html",
                     "application/oasis-html",
                     "empty",
                     1)
    # The datfile contains a list of variations.
    DB.create_qt_att(qt_id,
                     "datfile.txt",
                     "application/oasis-dat",
                     "0",
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

    # They entered something into the html field and didn't upload a
    # qtemplate.html
    if not ('newattachmentname' in form and
            form['newattachmentname'] == "qtemplate.html"):
        if 'newhtml' in form:
            html = form['newhtml'].encode("utf8")
            DB.create_qt_att(qt_id,
                             "qtemplate.html",
                             "text/plain",
                             html,
                             version)

    # They uploaded a new qtemplate.html
    if 'newindex' in files:
        data = files['newindex'].read()
        if len(data) > 1:
            html = data
            DB.create_qt_att(qt_id,
                             "qtemplate.html",
                             "text/plain",
                             html,
                             version)

    # They uploaded a new datfile
    if 'newdatfile' in files:
        data = files['newdatfile'].read()
        if len(data) > 1:
            DB.create_qt_att(qt_id,
                             "datfile.txt",
                             "text/plain",
                             data,
                             version)
            qvars = parse_datfile(data)
            for row in range(0, len(qvars)):
                DB.add_qt_variation(qt_id, row + 1, qvars[row], version)

                # They uploaded a new image file
    if 'newimgfile' in files:
        data = files['newimgfile'].read()
        if len(data) > 1:
            df = data
            DB.create_qt_att(qt_id, "image.gif", "image/gif", df, version)

    if 'newmodule' in form:
        try:
            newmodule = int(form['newmodule'])
        except (ValueError, TypeError):
            L.warn("QEditor: invalid value for newmodule received. Ignoring. '%s'" % form['newmodule'])
        else:
            DB.update_qt_marker(qt_id, newmodule)

    if 'newmaxscore' in form:
        try:
            newmaxscore = float(form['newmaxscore'])
        except (ValueError, TypeError):
            L.warn("QEditor: invalid value for newmaxscore received. Ignoring. '%s'" % form['newmaxscore'])
            newmaxscore = None
        DB.update_qt_maxscore(qt_id, newmaxscore)

    newname = False
    if 'newattachmentname' in form:
        if len(form['newattachmentname']) > 1:
            newname = form['newattachmentname']
    if 'newattachment' in files:
        fptr = files['newattachment']
        if not newname:
            # If they haven't supplied a filename we use
            # the name of the file they uploaded.
            # TODO: Do we need a security check? We don't create disk files with this name
            newname = fptr.filename
        if len(newname) < 1:
            L.info("File with no name uploaded by %s" % (session['username']))
            newname = 'NONAME'
        data = fptr.read()
        mtype = fptr.content_type

        if len(data) >= 1:
            DB.create_qt_att(qt_id, newname, mtype, data, version)
            L.info("File '%s' uploaded by %s" % (newname, session['username']))


def parse_datfile(datfile):
    """Convert the given datfile into a list of dictionaries of variables."""
    varbs = []
    for line in datfile.split('\n')[1:]:
        if len(line) > 2:
            varbs.append(parse_datline(line))
    return varbs


def parse_datline(datline):
    """Convert the given datline into a dictionary of variables. """
    qvars = {}
    varstring = "OAV=1"
    answers = ""
    valuepart = ""

    parts = datline.split('|')
    if len(parts) == 1:
        answers = datline
    elif len(parts) == 2:
        (valuepart, answers) = parts
    elif len(parts) == 3:
        (valuepart, answers, varstring) = parts

    corrects = answers.split(',')

    if len(varstring) > 1:
        varlist = varstring.split(',')
        if varlist:
            for v in varlist:
                try:
                    (a, b) = v.split("=")
                except (ValueError, AttributeError):
                    L.info("Bad line: '%s'" % v)
                    continue
                #                try:
                #                    QVars[a] = float(b)
                #                except:
                qvars[a] = b
        values = valuepart.split(';')
    else:
        return False

    valcount = 1
    vals = {}
    if values:
        if len(values) >= 1:
            for i in values:
                tmp = i.split(",", 3)
                if len(tmp) == 3:
                    (x, y, v) = tmp
                    if (x > -1) and (y > -1):
                        qvars["X%d" % (valcount,)] = x
                        qvars["Y%d" % (valcount,)] = y
                        qvars["Z%d" % (valcount,)] = v
                    vals[valcount] = v
                    valcount += 1

    tolerance = 1.0
    for i in range(0, len(corrects)):
        try:
            tolerance = 1.0
            qvars["A%d" % (i + 1,)] = float(corrects[i])
        except (TypeError, ValueError):
            # Presumably it's not a straight number
            # See if it has a tolerance attached
            try:
                (correct, tolerance) = corrects[i].split(":", 2)
                correct = float(correct)
                tolerance = float(tolerance)
                qvars["A%d" % (i + 1,)] = float(correct)
            except (TypeError, ValueError):
                # Nope, perhaps it's a string or something
                correct = "%s" % (corrects[i],)
                qvars["A%d" % (i + 1,)] = correct

        qvars["T%d" % (i + 1,)] = tolerance
        qvars["M%d" % (i + 1,)] = 0
        qvars["C%d" % (i + 1,)] = "Incorrect"

    return qvars


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
