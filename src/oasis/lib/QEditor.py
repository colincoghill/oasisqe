# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

"""Provides a question editing interface to the user."""

from oasis.lib import DB
from oasis.lib import Audit
from logging import getLogger
import re

L = getLogger("oasisqe")

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
    entries = Audit.get_records_by_object(qtid, 3, limit=100, offset=0)
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
