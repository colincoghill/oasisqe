# -*- coding: utf-8 -*-


""" A collection of functions that may be called by
    scripts. eg. the __marker.py and __results.py scripts.
"""
import OaDB
from Audit import audit


# We dont want the scripts playing with their questionID (qid) so we have to
# wrap all the functions that need it as an argument.


def withinTolerance(guess, correct, tolerance):
    """ Is the guess within tolerance % of the correct answer?
    """

    try:
        lower = correct - (abs(correct) * (tolerance / 100))
        upper = correct + (abs(correct) * (tolerance / 100))
    except (TypeError, ValueError):
        lower = None
        upper = None

    if upper < lower :
        tmp = lower
        lower = upper
        upper = tmp

    try:
        guess = float(guess)
    except (ValueError, TypeError):
        guess = None

    # noinspection PyComparisonWithNone
    if guess == None:  # guess could be 0
        return False

    if lower <= guess <= upper:
        return True

    return False


def marker_log_fn(qid):

    def real_markerlog(priority, mesg):
        """__marker.py has log() 'ed an error"""
        question_log(qid, priority, '__marker.py', mesg)

    return real_markerlog


def result_log_fn(qid):

    def real_resultlog(priority, mesg):
        """__result.py has log() 'ed an error"""
        question_log(qid, priority, '__result.py', mesg)

    return real_resultlog


def question_log(qid, priority, facility, mesg):
    """function for question scripts (marker, render, generator, etc) to
       use to log messages. """
    qid = int(qid)
    version = OaDB.getQuestionVersion(qid)
    variation = OaDB.getQuestionVariation(qid)
    qtid = OaDB.getQuestionParent(qid)
    owner = OaDB.getQTemplateOwner(qtid)
    audit(3, owner, qtid, "qlogger", "version=%s,variation=%s,priority=%s,facility=%s,message=%s" % (version, variation, priority, facility, mesg))

