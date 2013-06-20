# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Courses.py
    Handle course related operations.
"""
from oasis.lib import Topics, Groups

from oasis.lib.DB import run_sql, dbpool, MC
from logging import log, ERROR
import datetime

# WARNING: name and title are stored in the database as: title, description


def get_version():
    """ Fetch the current version of the course table.
        This will be incremented when anything in the courses table is changed.
        The idea is that while the version hasn't changed, course information
        can be cached in memory.
    """
    key = "coursetable-version"
    obj = MC.get(key)
    if obj:
        return int(obj)
    ret = run_sql("SELECT last_value FROM courses_version_seq;")
    if ret:
        MC.set(key, int(ret[0][0]))
        return int(ret[0][0])
    log(ERROR, "Error fetching Courses version.")
    return -1


def incr_version():
    """ Increment the course table version."""
    key = "coursetable-version"
    MC.delete(key)
    ret = run_sql("SELECT nextval('courses_version_seq');")
    if ret:
        MC.set(key, int(ret[0][0]))
        return int(ret[0][0])
    log(ERROR, "Error incrementing Courses version.")
    return -1


def set_name(course_id, name):
    """ Set the name of a course."""
    assert isinstance(course_id, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    incr_version()
    run_sql("UPDATE courses SET title=%s WHERE course=%s;", (name, course_id))
    key = "course-%s-name" % course_id
    MC.delete(key)


def set_title(course_id, title):
    """ Set the title of a course."""
    assert isinstance(course_id, int)
    assert isinstance(title, str) or isinstance(title, unicode)
    incr_version()
    run_sql("UPDATE courses SET description=%s WHERE course=%s;",
            (title, course_id))
    key = "course-%s-title" % course_id
    MC.delete(key)


def get_active(course_id):
    """ Fetch the active flag"""
    assert isinstance(course_id, int)
    key = "course-%s-active" % course_id
    obj = MC.get(key)
    if not obj is None:
        return obj
    ret = run_sql("SELECT active FROM courses WHERE course=%s;", (course_id,))
    if ret:
        MC.set(key, ret[0][0])
        return ret[0][0]
    log(ERROR, "Request for active flag of unknown course %s." % course_id)
    return None


def set_active(course_id, active):
    """ Set the active flag of a course."""
    assert isinstance(course_id, int)
    assert isinstance(active, bool)
    if active:
        val = 1
    else:
        val = 0
    run_sql("UPDATE courses SET active=%s WHERE course=%s;", (val, course_id))
    incr_version()
    key = "course-%s-active" % course_id
    MC.delete(key)
    key = "courses-active"
    MC.delete(key)


def set_prac_vis(cid, visibility):
    """ Who can do practice questions."""
    assert isinstance(cid, int)
    assert isinstance(visibility, str) or isinstance(visibility, unicode)

    run_sql("UPDATE courses SET practice_visibility=%s WHERE course=%s;",
            (visibility, cid))
    incr_version()


def set_assess_vis(cid, visibility):
    """ Who can do assessments."""
    assert isinstance(cid, int)
    assert isinstance(visibility, str) or isinstance(visibility, unicode)

    run_sql("UPDATE courses SET assess_visibility=%s WHERE course=%s;",
            (visibility, cid))
    incr_version()


def get_users(course_id):
    """ Return a list of users in the course"""
    allusers = []
    for g_id, group in Groups.active_by_course(course_id).iteritems():
        allusers.append(group.members())
    return allusers


def get_all(only_active=True):
    """ Return a list of all courses in the system."""
    if only_active:
        sql = """SELECT course FROM courses WHERE active=1 ORDER BY title;"""
        key = "courses-active"
    else:
        sql = """SELECT course FROM courses ORDER BY title;"""
        key = "courses-all"
    obj = MC.get(key)
    if obj:
        return obj
    ret = run_sql(sql)
    if ret:
        courses = [int(row[0]) for row in ret]
        MC.set(key, courses)
        return courses
    return []


def get_courses_dict():
    """ Return a summary of all courses, keyed by course id
        [id] = { 'id':id, 'name':name, 'title':title }
    """
    ret = run_sql(
        """SELECT course, title, description, owner, active, type,
                  practice_visibility, assess_visibility
             FROM courses;""")
    cdict = {}
    if ret:
        for row in ret:
            course = {
                'id': int(row[0]),
                'name': row[1],
                'title': row[2],
                'owner': row[3],
                'active': row[4],
                'type': row[5],
                'practice_visibility': row[6],
                'assess_visibility': row[7]
            }

            if not course['practice_visibility']:
                course['practice_visibility'] = "all"
            if not course['assess_visibility']:
                course['assess_visibility'] = "all"
            cdict[int(row[0])] = course
    return cdict


def get_course_by_name(name):
    """ Return a course dict for the given name, or None
         { 'id':id, 'name':name, 'title':title }
    """
    ret = run_sql(
        """SELECT course, title, description, owner, active, type,
                  practice_visibility, assess_visibility
           FROM courses
           WHERE lower(title) LIKE lower(%s);""", (name,))
    course = None
    if ret:
        row = ret[0]
        course = {
                'id': int(row[0]),
                'name': row[1],
                'title': row[2],
                'owner': row[3],
                'active': row[4],
                'type': row[5],
                'practice_visibility': row[6],
                'assess_visibility': row[7]
        }

        if not course['practice_visibility']:
            course['practice_visibility'] = "all"
        if not course['assess_visibility']:
            course['assess_visibility'] = "all"

    return course


def create(name, description, owner, coursetype):
    """ Add a course to the database."""
    conn = dbpool.begin()
    conn.run_sql("""INSERT INTO courses (title, description, owner, type)
                    VALUES (%s, %s, %s, %s);""",
                    (name, description, owner, coursetype))
    res = conn.run_sql("SELECT currval('courses_course_seq')")
    dbpool.commit(conn)
    incr_version()
    key = "courses-active"
    MC.delete(key)
    key = "courses-all"
    MC.delete(key)
    if res:
        return int(res[0][0])
    log(ERROR,
        "create('%s','%s',%d,%d) Fail" % (name, description, owner, coursetype))
    return 0


def get_groups(course_id):
    """ Return a dict of groups currently attached to this course."""

    return Groups.active_by_course(course_id)


def add_group(group_id, course_id):
    """ Add a group to a course."""
    sql = "INSERT INTO groupcourses (groupid, active, course) " \
          "VALUES (%s, %s, %s);"
    params = (group_id, 1, course_id)
    run_sql(sql, params)


def del_group(group_id, course_id):
    """ Remove a group from the course."""
    assert isinstance(group_id, int)
    assert isinstance(course_id, int)

    sql = "DELETE FROM groupcourses" \
          " WHERE groupid=%s AND course=%s;"
    params = (group_id, course_id)
    run_sql(sql, params)



def get_topics_all(course, archived=2, numq=True):
    """ Return a summary of all topics in the course.
        if archived=0, only return non archived courses
        if archived=1, only return archived courses
        if archived=2, return all courses
        if numq is true then include the number of questions in the topic
    """
    ret = None
    if archived == 0:
        ret = run_sql("""SELECT topic, title, position, visibility, archived
                         FROM topics
                         WHERE course=%s
                           AND (archived='0' OR archived IS NULL)
                         ORDER BY position, topic;""", (course,))
    elif archived == 1:
        ret = run_sql("""SELECT topic, title, position, visibility, archived
                         FROM topics
                         WHERE course=%s
                           AND archived='1'
                         ORDER BY position, topic;""", (course,))
    elif archived == 2:
        ret = run_sql("""SELECT topic, title, position, visibility, 0
                         FROM topics
                         WHERE course=%s
                         ORDER BY position, topic;""", (course,))
    info = {}
    if ret:
        count = 0
        for row in ret:
            info[count] = {'id': int(row[0]),
                           'title': row[1],
                           'position': row[2],
                           'visibility': row[3],
                           'archived': row[4]}
            if numq:
                info[count]['numquestions'] = Topics.get_num_qs(int(row[0]))
            count += 1
    else:  # we probably don't have the archived flag in the Db yet
        ret = run_sql(
            """SELECT topic, title, visibility
               FROM topics
               WHERE course=%s
               ORDER BY position, topic;""", (course,))
        if ret:
            count = 0
            for row in ret:
                info[count] = {'id': int(row[0]),
                               'title': row[1],
                               'visibility': row[2]}
                if numq:
                    info[count]['numquestions'] = Topics.get_num_qs(int(row[0]))
                count += 1
    return info


def get_topics(cid):
    """ Return a list of all topics in the course."""
    key = "course-%s-topics" % cid
    obj = MC.get(key)
    if obj:
        return obj
    sql = "SELECT topic FROM topics WHERE course=%s ORDER BY position;"
    params = (cid,)
    ret = run_sql(sql, params)
    if ret:
        topics = [row[0] for row in ret]
        MC.set(key, topics)
        return topics
    MC.set(key, [])
    return []


def get_exams(cid, prev_years=False):
    """ Return a list of all assessments in the course."""
    assert isinstance(cid, int)
    assert isinstance(prev_years, bool)
    if not prev_years:
        now = datetime.datetime.now()
        year = now.year
        sql = """SELECT exam
                 FROM exams
                 WHERE course=%s
                   AND archived='0'
                   AND "end" > '%s-01-01';"""
        params = (cid, year)
    else:
        sql = """SELECT exam FROM exams WHERE course=%s;"""
        params = (cid,)
    ret = run_sql(sql, params)
    if ret:
        exams = [int(row[0]) for row in ret]
        return exams
    return []


def create_config(course_id, coursetemplate, courserepeat):
    """ Course is being created. Setup some configuration depending on
        given values.
    """

    # First, course template

    # demonstration
    #    Create a staff group
    #    Create a student group set to open registration
    #    Create a student group set to ad-hoc



    pass
