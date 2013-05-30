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
# every 10 mins or something.

# Get the latest version of the course info
# We can cache information until this changes, then we
# need to flush and reread it from the Db layer
# version will be bumped when any of the following changes:
# course name, title, active, usersincourse, examsincourse, topicsincourse
from oasis.lib import Courses

COURSES_VERSION = -1

COURSES = {}


def loadCourses():
    """Read the list of courses into memory """
    global COURSES
    log(INFO, "Courses fetched from database.")
    COURSES = Courses.getFullCourseDict()


def reloadCoursesIfNeeded():
    """If the course table has changed, reload the info. """
    global COURSES_VERSION
    newversion = Courses.get_version()
    if newversion > COURSES_VERSION:
        COURSES_VERSION = newversion
        loadCourses()
    return


def getCourseDict(only_active=True):
    """ Return a dictionary of courses.
        By default only active courses.
        key will be course ID.

        courses[cid] = {id:, name:, title:}
    """
    cdict = {}
    reloadCoursesIfNeeded()
    for course in COURSES:
        if only_active:
            if COURSES[course]['active'] == 1:
                cdict[course] = COURSES[course]
        else:
            cdict[course] = COURSES[course]

    return cdict


def getCourseList(only_active=True, sortedby="name"):
    """ Return a list of courses.
        By default only active courses.
        will be ordered by given field.

       [{id:, name:, title:}, ]
    """
    clist = []
    reloadCoursesIfNeeded()
    for course in COURSES:
        if only_active:
            if COURSES[course]['active'] == 1:
                clist.append(COURSES[course])
        else:
            clist.append(COURSES[course])

    clist.sort(lambda f, s: cmp(f[sortedby], s[sortedby]))
    return clist


def getTopicsInCourse(cid, archived=2):
    """ Return a dict of all topics in the course. """
    reloadCoursesIfNeeded()
    if not "topics" in COURSES[cid]:
        COURSES[cid]['topics'] = Courses.getTopicsInfoAll(cid, archived, True)
    return COURSES[cid]['topics']


def get_topics_list(course_id, archived=2):
    """ Return a list of all topics in the course.
    """

    reloadCoursesIfNeeded()
    if not "topics" in COURSES[course_id]:
        COURSES[course_id]['topics'] = Courses.getTopicsInfoAll(course_id, archived, True)
    topics = COURSES[course_id]['topics']
    tlist = [topics[tid] for tid in topics]
    return tlist


def get_course(course_id):
    """ Return a dict of the course fields.
    """

    reloadCoursesIfNeeded()
    return COURSES[course_id]


reloadCoursesIfNeeded()