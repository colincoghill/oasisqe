# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" db/Topics.py
    Handle topic related operations.
"""
import json

from .DB import dbpool, run_sql, MC
from logging import log, ERROR, INFO


def create(course_id, name, vis, pos=1):
    """Add a topic to the database."""
    key = "course-%s-topics" % course_id
    MC.delete(key)
    log(INFO,
        "db/Topics/create(%s, %s, %s, %s)" % (course_id, name, vis, pos))
    conn = dbpool.begin()
    conn.run_sql("""INSERT INTO topics (course, title, visibility, position)
                    VALUES (%s, %s, %s, %s);""",
                    (course_id, name, vis, pos))
    res = conn.run_sql("SELECT currval('topics_topic_seq');")
    dbpool.commit(conn)
    if res:
        return res[0][0]
    log(ERROR,
        "Topic create error (%s, %s, %s, %s)" % (course_id, name, vis, pos))
    return 0


def getTopic(topic_id):
    """ Fetch a dictionary of topic values"""
    key = "topic-%s-record" % topic_id
    obj = MC.get(key)
    if obj:
        return json.loads(obj)
    sql = """SELECT topic, course, title, visibility, position, archived
             FROM topics
             WHERE topic=%s;"""
    params = (topic_id,)
    ret = run_sql(sql, params)
    if not ret:
        raise KeyError("Unable to find topic %s" % topic_id)
    row = ret[0]
    topic = {
        'id': row[0],
        'course': row[1],
        'title': row[2],
        'visibility': row[3],
        'position': row[4],
        'archived': row[5]
    }
    if topic['position'] is None:
        topic['position'] = 0
    MC.set(key, json.dumps(topic))
    return topic


def get_name(topic_id):
    """Fetch the name of a topic."""
    return getTopic(topic_id)['title']


def setName(topic_id, name):
    """Set the name of a topic."""
    assert isinstance(topic_id, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    run_sql("UPDATE topics SET title=%s WHERE topic=%s;", (name, topic_id))
    key = "topic-%s-record" % topic_id
    MC.delete(key)


def getPosition(topic_id):
    """Fetch the position of a topic."""
    assert isinstance(topic_id, int)
    return getTopic(topic_id)['position']


def setPosition(topic_id, pos):
    """Update the position of a topic."""
    if pos is None:
        pos = 0
    run_sql("""UPDATE topics
               SET position=%s
               WHERE topic=%s;""", (pos, topic_id))
    key = "topic-%s-record" % topic_id
    MC.delete(key)
    course = get_course_id(topic_id)
    key = "course-%s-topics" % course
    MC.delete(key)


def get_course_id(topic_id):
    """Fetch the course ID of the course a topic belongs to"""
    return getTopic(topic_id)['course']


def getVisibility(topic_id):
    """Fetch the visibility of a topic."""
    return getTopic(topic_id)['visibility']


def setVisibility(topic_id, vis):
    """Update the visibility of a topic."""
    run_sql("""UPDATE topics SET visibility=%s WHERE topic=%s;""", (vis, topic_id))
    key = "topic-%s-record" % topic_id
    MC.delete(key)


def get_num_qs(topic_id):
    """Tell us how many questions are in the given topic."""
    key = "topic-%s-numquestions" % topic_id
    obj = MC.get(key)
    if obj:
        return int(obj)
    sql = """SELECT count(topic)
            FROM questiontopics
            WHERE topic=%s
             AND position > 0;
            """
    params = (topic_id,)
    try:
        res = run_sql(sql, params)
        if not res:
            num = 0
        else:
            num = int(res[0][0])
        MC.set(key, num, 180) # 3 minute cache
        return num
    except LookupError:
        raise IOError, "Database connection failed"


def get_qts(topic_id):
    """ Return a dictionary of the QTemplates in the given Topic, keyed by qtid.
        qtemplates[qtid] = {'id', 'position', 'owner', 'name', 'description',
                            'marker', 'maxscore', 'version', 'status'}
    """
    sql = """select qtemplates.qtemplate, questiontopics.position,
                qtemplates.owner, qtemplates.title, qtemplates.description,
                qtemplates.marker, qtemplates.scoremax, qtemplates.version,
                qtemplates.status
            from questiontopics,qtemplates
            where questiontopics.topic=%s
            and questiontopics.qtemplate = qtemplates.qtemplate;"""
    params = (topic_id,)
    ret = run_sql(sql, params)
    qtemplates = {}
    if ret:
        for row in ret:
            qtid = int(row[0])
            pos = int(row[1])
            owner = int(row[2])
            name = row[3]
            desc = row[4]
            marker = row[5]
            scoremax = row[6]
            version = int(row[7])
            status = row[8]
            qtemplates[qtid] = {'id': qtid,
                                'position': pos,
                                'owner': owner,
                                'name': name,
                                'description': desc,
                                'marker': marker,
                                'maxscore': scoremax,
                                'version': version,
                                'status': status}
    return qtemplates
