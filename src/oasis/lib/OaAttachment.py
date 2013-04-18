# -*- coding: utf-8 -*-

"""OaAttachment.py
 Send a question attachment
 This is a little more advanced than OaQuestionAtt, as we need to be aware of different kinds of attachment.
"""

from oasis.lib import OaDB

def is_restricted(fname):
    """ Is the filename restricted - not to be downloaded by non question editors? """
    if fname in ('datfile.txt', 'datfile.dat', 'qtemplate.html', 'marker.py', 'results.py'):
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
        filename = OaDB.getQAttachmentFilename(qtid, name, variation, version)
        if filename:
            return OaDB.getQAttachmentMimeType(qtid, name, variation, version), filename
        filename = OaDB.getQTAttachmentFilename(qtid, name, version)
        if filename:
            return OaDB.getQTAttachmentMimeType(qtid, name, version), filename
    else:
        filename = OaDB.getQTAttachmentFilename(qtid, name, version)
        if filename:
            return OaDB.getQTAttachmentMimeType(qtid, name, version), filename
        filename = OaDB.getQAttachmentFilename(qtid, name, variation, version)
        if filename:
            return OaDB.getQAttachmentMimeType(qtid, name, variation, version), filename
    return None, None
