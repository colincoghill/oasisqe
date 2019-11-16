# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" A collection of functions that may be called by
    scripts. eg. the __marker.py and __results.py scripts.
"""
from . import DB
from .Audit import audit


# We don't want the scripts playing with their questionID (qid) so we have to
# wrap all the functions that need it as an argument.


def within_tolerance(guess, correct, tolerance):

    """ Is the guess within tolerance % of the correct answer?
        If correct answer is 0.0, we check between -tolerance and + tolerance

        :param guess: a guess value, eg. 3.25
        :type guess: float
        :param correct: the correct answer, eg. 3.249
        :type correct: float
        :param tolerance: the percentage tolerance to compare with
        :type tolerance: float or int
        :rtype: bool

        :example:
        >>> within_tolerance("3.429", 3.43, 10)
        False
        >>> within_tolerance("3.429", 3.43, 1)
        False
        >>> within_tolerance(0.01, 0, 10)
        True
        >>>
    """

    try:
        tolerance = float(tolerance)
    except (TypeError, ValueError):
        raise ValueError("Tolerance of '%s' is not valid." % tolerance)

    try:
        correct = float(correct)
    except (TypeError, ValueError):
        raise ValueError("Correct answer of '%s' is not a number." % correct)

    try:
        lower = correct - (abs(correct) * (tolerance / 100))
        upper = correct + (abs(correct) * (tolerance / 100))
    except (TypeError, ValueError):
        lower = None
        upper = None

    if upper < lower:
        lower, upper = upper, lower

    try:
        guess = float(guess)
    except (ValueError, TypeError):
        guess = None

    if correct == 0.0:
        lower = -(tolerance / 100)
        upper = tolerance / 100

    # noinspection PyComparisonWithNone
    if guess is None:  # guess could be 0
        return False

    # print "lower,guess,upper, correct => ", lower, guess, upper, correct

    if lower <= guess <= upper:
        return True

    return False


def marker_log_fn(qid):
    """ When a marker script wishes to log an error, it comes through here.
    """
    def real_markerlog(priority, mesg):
        """__marker.py has log() 'ed an error"""
        q_log(qid, priority, '__marker.py', mesg)

    return real_markerlog


def result_log_fn(qid):
    """ When a result script wishes to log an error, it comes through here.
    """
    def real_resultlog(priority, mesg):
        """__result.py has log() 'ed an error"""
        q_log(qid, priority, '__result.py', mesg)

    return real_resultlog


def q_log(qid, priority, facility, mesg):
    """function for question scripts (marker, render, generator, etc) to
       use to log messages. """
    qid = int(qid)
    version = DB.get_q_version(qid)
    variation = DB.get_q_variation(qid)
    qtid = DB.get_q_parent(qid)
    owner = DB.get_qt_owner(qtid)
    audit(3, owner, qtid, "qlogger", "version=%s,variation=%s,priority=%s,facility=%s,message=%s" % (version, variation, priority, facility, mesg))
