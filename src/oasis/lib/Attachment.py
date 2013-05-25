# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

"""OaAttachment.py
 Send a question attachment
 This is a little more advanced than OaQuestionAtt, as we need to be aware
 of different kinds of attachment.
"""

from oasis.lib import DB

def is_restricted(fname):
    """ Is the filename restricted
        - not to be downloaded by non question editors?
    """
    if fname in ('datfile.txt', 'datfile.dat', 'qtemplate.html',
                 'marker.py', 'results.py'):
        return True
    if fname.startswith("_"):
        return True
    if fname.endswith(".oqe"):
        return True
    return False


def getQuestionAttachmentDetails(qtid, version, variation, name):
    """ Find a question attachment and return its details. """
    # for the two biggies we hit the question first,
    # otherwise check the question template first
    if name == "image.gif" or name == "qtemplate.html":
        filename = DB.get_q_att_fname(qtid, name, variation, version)
        if filename:
            return DB.get_q_att_mimetype(qtid, name, variation, version), filename
        filename = DB.getQTAttachmentFilename(qtid, name, version)
        if filename:
            return DB.get_qt_att_mimetype(qtid, name, version), filename
    else:
        filename = DB.getQTAttachmentFilename(qtid, name, version)
        if filename:
            return DB.get_qt_att_mimetype(qtid, name, version), filename
        filename = DB.get_q_att_fname(qtid, name, variation, version)
        if filename:
            return DB.get_q_att_mimetype(qtid, name, variation, version), filename
    return None, None
