# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Fast interface for access to Course information.
    List of courses is small, so we can load it all into memory for speed
    and to take some pressure off the database layer.
"""

from logging import log, INFO

# Todo: this may misbehave when we're running parallel web servers.
# Maybe make it expire automatically
# every 10 mins or something. Or throw it all out and use flask-caching

# Get the latest version of the course info
# We can cache information until this changes, then we
# need to flush and reread it from the Db layer
# version will be bumped when any of the following changes:
# course name, title, active, usersincourse, examsincourse, topicsincourse
from oasis.lib import Courses

COURSES_VERSION = -1

COURSES = {}


def load_courses():
    """Read the list of courses into memory """
    global COURSES
    log(INFO, "Courses fetched from database.")
    COURSES = Courses.get_courses_dict()


def reload_if_needed():
    """If the course table has changed, reload the info. """
    global COURSES_VERSION
    newversion = Courses.get_version()
    if newversion > COURSES_VERSION:
        COURSES_VERSION = newversion
        load_courses()
    return


def get_course_dict(only_active=True):
    """ Return a dictionary of courses.
        By default only active courses.
        key will be course ID.

        courses[cid] = {id:, name:, title:}
    """
    cdict = {}
    reload_if_needed()
    for course in COURSES:
        if only_active:
            if COURSES[course]['active'] == 1:
                cdict[course] = COURSES[course]
        else:
            cdict[course] = COURSES[course]

    return cdict


def get_course_list(only_active=True, sortedby="name"):
    """ Return a list of courses.
        By default only active courses.
        will be ordered by given field.

       [{id:, name:, title:}, ]
    """
    clist = []
    reload_if_needed()
    for course in COURSES:
        if only_active:
            if COURSES[course]['active'] == 1:
                clist.append(COURSES[course])
        else:
            clist.append(COURSES[course])

    clist.sort(lambda f, s: cmp(f[sortedby], s[sortedby]))
    return clist


def get_topics(cid, archived=2):
    """ Return a dict of all topics in the course. """
    reload_if_needed()
    if "topics" not in COURSES[cid]:
        COURSES[cid]['topics'] = Courses.get_topics_all(cid, archived, True)
    return COURSES[cid]['topics']


def get_topics_list(course_id, archived=2):
    """ Return a list of all topics in the course.
    """

    reload_if_needed()
    if "topics" not in COURSES[course_id]:
        COURSES[course_id]['topics'] = Courses.get_topics_all(course_id, archived, True)
    topics = COURSES[course_id]['topics']
    tlist = [topics[tid] for tid in topics]
    return tlist


def get_course(course_id):
    """ Return a dict of the course fields.
    """

    reload_if_needed()
    if course_id not in COURSES:
        load_courses()
    return COURSES[course_id]

