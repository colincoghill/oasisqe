# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" OaDB.py
    This provides a collection of methods for accessing the database.
    If the database is changed to something other than postgres, this
    is where to start.
"""

import psycopg2
import cPickle
import datetime
import json
import os
import OaConfig
import Pool
from logging import getLogger

L = getLogger("oasisqe.db")

IntegrityError = psycopg2.IntegrityError

# 3 connections. Lets us keep going if one is slow but
# doesn't overload the server if there're a lot of us
dbpool = Pool.DbPool(OaConfig.oasisdbconnectstring, 3)


from Pool import MCPool

# Get a pool of memcache connections to use
MC = MCPool('127.0.0.1:11211', 3)


def run_sql(sql, params=None, quiet=False):
    """ Execute SQL commands using the dbpool"""
    L.debug("SQL: %s ;(%s)", sql, params)
    conn = dbpool.start()
    res = conn.run_sql(sql, params, quiet=quiet)
    dbpool.finish(conn)
    return res


def set_q_viewtime(question):
    """ Record that the question has been viewed.
        Not a good idea to call multiple times since it's
        nearly always the first time that we want.
    """
    assert isinstance(question, int)
    run_sql("""UPDATE questions
               SET firstview=NOW()
               WHERE question=%s;""", (question,))


def set_q_marktime(question):
    """ Record that the question was marked.
        Probably best not to call multiple times since
        we usually want the first time.
    """
    assert isinstance(question, int)
    run_sql("""UPDATE questions
               SET marktime=NOW()
               WHERE question=%s;""", (question,))


def get_q_viewtime(question):
    """ Return the time that the question was first viewed
        as a human readable string.
    """
    assert isinstance(question, int)
    ret = run_sql("""SELECT firstview
                     FROM questions
                     WHERE question=%s;""", (question,))
    if ret:
        firstview = ret[0][0]
        if firstview:
            return firstview.strftime("%Y %b %d, %I:%M%P")
    return None


def get_q_marktime(question):
    """ Return the time that the question was marked
        as a human readable string, or None if it hasn't been.
    """
    assert isinstance(question, int)
    ret = run_sql("""SELECT marktime
                     FROM questions
                     WHERE question=%s;""", (question,))
    if ret:
        marktime = ret[0][0]
        if marktime:
            return marktime.strftime("%Y %b %d, %I:%M%P")
    return None


def get_exam_q_by_pos_student(exam, position, student):
    """ Return the question at the given position in the exam for the student.
        Return False if there is no question assigned yet.
    """
    assert isinstance(exam, int)
    assert isinstance(position, int)
    assert isinstance(student, int)
    ret = run_sql("""SELECT question FROM examquestions
                        WHERE student = %s
                        AND position = %s
                        AND exam = %s;""", (student, position, exam))
    if ret:
        return int(ret[0][0])
    return False


def get_exam_q_by_qt_student(exam, qt_id, student):
    """ Fetch an assessment question by student"""
    assert isinstance(exam, int)
    assert isinstance(qt_id, int)
    assert isinstance(student, int)
    ret = run_sql("""SELECT question FROM questions
                        WHERE student=%s
                        AND qtemplate=%s
                        AND exam=%s;""", (student, qt_id, exam))
    if ret:
        return int(ret[0][0])
    return False


def get_q_by_qt_student(qt_id, student):
    """ Fetch a question by student"""
    assert isinstance(qt_id, int)
    assert isinstance(student, int)
    ret = run_sql("""SELECT question FROM questions
                        WHERE student = %s
                        AND qtemplate = %s and status = '1'
                        AND exam = '0'""", (student, qt_id))
    if ret:
        return int(ret[0][0])
    return False


def update_q_score(q_id, score):
    """ Set the score of a question."""
    assert isinstance(q_id, int)
    try:
        sc = float(score)
    except (TypeError, ValueError):
        L.error("Unable to cast score to float!? '%s'" % score)
        return
    L.debug("Setting question %s score to %s" % (q_id, score))
    run_sql("""UPDATE questions SET score=%s WHERE question=%s;""",
            ("%.1f" % sc, q_id))


def set_q_status(q_id, status):
    """ Set the status of a question."""
    assert isinstance(q_id, int)
    assert isinstance(status, int)
    run_sql("UPDATE questions SET status=%s WHERE question=%s;", (status, q_id))


def get_q_version(q_id):
    """ Return the template version this question was generated from """
    assert isinstance(q_id, int)
    ret = run_sql("SELECT version FROM questions WHERE question=%s;", (q_id,))
    if ret:
        return int(ret[0][0])
    return None


def get_q_variation(q_id):
    """ Return the template variation this question was generated from"""
    assert isinstance(q_id, int)
    ret = run_sql("SELECT variation FROM questions WHERE question=%s;", (q_id,))
    if ret:
        return int(ret[0][0])
    return None


def get_q_parent(q_id):
    """ Return the template this question was generated from"""
    assert isinstance(q_id, int)
    ret = run_sql("SELECT qtemplate FROM questions WHERE question=%s;", (q_id,))
    if ret:
        return int(ret[0][0])
    L.error("No parent found for question %s!" % q_id)
    return None


def save_guess(q_id, part, value):
    """ Store the guess in the database."""
    assert isinstance(q_id, int)
    assert isinstance(part, int)
    assert isinstance(value, unicode)
    L.info("Saving guess for qid %s:  %s = %s " % (q_id, part, value))
    # noinspection PyComparisonWithNone
    if value is not None:  # "" is legit
        run_sql("""INSERT INTO guesses (question, created, part, guess)
                   VALUES (%s, NOW(), %s, %s);""", (q_id, part, value))


def get_q_guesses(q_id):
    """ Return a dictionary of the recent guesses in a question."""
    assert isinstance(q_id, int)
    ret = run_sql("""SELECT part, guess
                     FROM guesses
                     WHERE question = %s
                     ORDER BY created DESC;""", (q_id,))
    if not ret:
        return {}
    guesses = {}
    for row in ret:
        if not "G%d" % (int(row[0])) in guesses:
            guesses["G%d" % (int(row[0]))] = row[1]
    return guesses


def get_q_guesses_before_time(q_id, lasttime):
    """ Return a dictionary of the recent guesses in a question,
        from before it was marked.
    """
    assert isinstance(q_id, int)
    assert isinstance(lasttime, datetime.datetime)
    ret = run_sql("""SELECT part, guess
                     FROM guesses
                     WHERE question=%s
                       AND created < %s
                     ORDER BY created DESC;""",
                  (q_id, lasttime))
    if not ret:
        return {}
    guesses = {}
    for row in ret:
        if not "G%d" % (int(row[0])) in guesses:
            guesses["G%d" % (int(row[0]))] = row[1]
    return guesses


def get_qt_by_embedid(embed_id):
    """ Find the question template with the given embed_id,
        or raise KeyError if not found.
    """
    assert isinstance(embed_id, unicode)
    sql = "SELECT qtemplate FROM qtemplates WHERE embed_id=%s LIMIT 1;"
    params = (embed_id,)
    ret = run_sql(sql, params)
    if not ret:
        raise KeyError("Can't find qtemplate with embed_id = %s" % embed_id)
    row = ret[0]
    qtemplate = int(row[0])
    return qtemplate


def get_qtemplate(qt_id, version=None):
    """ Return a dictionary with the QTemplate information """
    assert isinstance(qt_id, int)
    assert isinstance(version, int) or version is None
    if version:
        sql = """SELECT qtemplate, owner, title, description,
                        marker, scoremax, version, status, embed_id
                 FROM qtemplates
                 WHERE qtemplate=%s
                   AND version=%s;"""
        params = (qt_id, version)
    else:
        sql = """SELECT qtemplate, owner, title, description,
                        marker, scoremax, version, status, embed_id
                 FROM qtemplates
                 WHERE qtemplate=%s
                 ORDER BY version DESC
                 LIMIT 1;"""
        params = (qt_id,)
    ret = run_sql(sql, params)
    if len(ret) == 0:
        raise KeyError("Can't find qtemplate %s, version %s" % (qt_id, version))
    row = ret[0]
    qtemplate = {
        'id': int(row[0]),
        'owner': int(row[1]),
        'title': row[2],
        'description': row[3],
        'marker': row[4],
        'scoremax': row[5],
        'version': int(row[6]),
        'status': int(row[7]),
        'embed_id': row[8]
    }
    if not qtemplate['embed_id']:
        qtemplate['embed_id'] = ""
    try:
        qtemplate['scoremax'] = float(qtemplate['scoremax'])
    except TypeError:
        qtemplate['scoremax'] = None
    return qtemplate


def update_qt_embedid(qt_id, embed_id):
    """ Set the QTemplate's embed_id"""
    assert isinstance(qt_id, int)
    assert isinstance(embed_id, unicode) or isinstance(embed_id, str)
    if embed_id == "":
        embed_id = None
    sql = "UPDATE qtemplates SET embed_id=%s WHERE qtemplate=%s"
    params = (embed_id, qt_id)
    if run_sql(sql, params) is False:  # could be [], which is success
        return False
    return True


def incr_qt_version(qt_id):
    """ Increase the version number of the current question template"""
    # FIXME: Not done in a parallel-safe manner. Could find a way to do this
    # in the database. Fairly low risk.
    assert isinstance(qt_id, int)
    version = int(get_qt_version(qt_id))
    version += 1
    run_sql("""UPDATE qtemplates
               SET version=%s
               WHERE qtemplate=%s;""", (version, qt_id))
    return version


def get_qt_version(qt_id):
    """ Fetch the version of a question template."""
    assert isinstance(qt_id, int)
    ret = run_sql("""SELECT version
                     FROM qtemplates
                     WHERE qtemplate=%s;""", (qt_id,))
    if ret:
        return int(ret[0][0])
    raise KeyError("Question Template version %s not found" % qt_id)


def get_qt_maxscore(qt_id):
    """ Fetch the maximum score of a question template."""
    assert isinstance(qt_id, int)
    key = "qtemplate-%d-maxscore" % (qt_id,)
    obj = MC.get(key)
    if obj is not None:  # 0 or [] or "" could be legit
        return obj
    ret = run_sql("""SELECT scoremax
                     FROM qtemplates
                     WHERE qtemplate=%s;""", (qt_id,))
    if ret:
        try:
            scoremax = float(ret[0][0])
        except (ValueError, TypeError, KeyError):
            scoremax = 0.0
        MC.set(key, scoremax)
        return scoremax
    raise KeyError("Question Template maxscore %s not found" % qt_id)


def get_qt_marker(qt_id):
    """ Fetch the marker of a question template."""
    assert isinstance(qt_id, int)
    ret = run_sql("SELECT marker FROM qtemplates WHERE qtemplate=%s;", (qt_id,))
    if ret:
        return int(ret[0][0])
    L.warn("Request for unknown question template %s." % qt_id)


def get_qt_owner(qt_id):
    """ Fetch the owner of a question template.
        (The last person to make changes to it)
    """
    assert isinstance(qt_id, int)
    ret = run_sql("SELECT owner FROM qtemplates WHERE qtemplate=%s;", (qt_id,))
    if ret:
        return ret[0][0]
    L.warn("Request for unknown question template %s." % qt_id)


def get_qt_name(qt_id):
    """ Fetch the name of a question template."""
    assert isinstance(qt_id, int)
    key = "qtemplate-%d-name" % qt_id
    obj = MC.get(key)
    if obj is not None:
        return obj
    ret = run_sql("SELECT title FROM qtemplates WHERE qtemplate=%s;", (qt_id,))
    if ret:
        MC.set(key, ret[0][0], expiry=360)  # 6 minutes
        return ret[0][0]
    L.warn("Request for unknown question template %s." % qt_id)


def get_qt_embedid(qt_id):
    """ Fetch the embed_id of a question template."""
    assert isinstance(qt_id, int)
    ret = run_sql("""SELECT embed_id
                     FROM qtemplates
                     WHERE qtemplate=%s;""", (qt_id,))
    if ret:
        embed_id = ret[0][0]
        if not embed_id:
            embed_id = ""
        return embed_id
    L.warn("Request for unknown question template %s." % qt_id)


def get_qt_atts(qt_id, version=1000000000):
    """ Return a list of (names of) all attachments connected to
        this question template.
    """
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    if version == 1000000000:
        version = get_qt_version(qt_id)
    ret = run_sql("SELECT name FROM qtattach WHERE qtemplate = %s "
                  "AND version <= %s GROUP BY name ORDER BY name;",
                  (qt_id, version))
    if ret:
        attachments = [att[0] for att in ret]
        return attachments
    return []


def get_q_att_mimetype(qt_id, name, variation, version=1000000000):
    """ Return a string containing the mime type of the attachment.
    """
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    assert isinstance(variation, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    if version == 1000000000:
        version = get_qt_version(qt_id)

    ret = run_sql("""SELECT qtemplate, mimetype
                     FROM qattach
                     WHERE name=%s
                       AND qtemplate=%s
                       AND variation=%s
                       AND version=%s
                  """, (name, qt_id, variation, version))
    if ret:
        return ret[0][1]
    # We use mimetype to see if an attachment is generated so
    # not finding one is no big deal.
    return False


def get_qt_att_mimetype(qt_id, name, version=1000000000):
    """ Fetch the mime type of a template attachment.
        If version is set to 0, will fetch the newest.
    """
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    if version == 1000000000:
        version = get_qt_version(qt_id)

    nameparts = name.split("?")
    if len(nameparts) > 1:
        name = nameparts[0]
    ret = run_sql("""SELECT mimetype
                        FROM qtattach
                        WHERE qtemplate = %s
                        AND name = %s
                        AND version = (SELECT MAX(version)
                            FROM qtattach
                            WHERE qtemplate=%s
                            AND version <= %s
                            AND name=%s)""",
                  (qt_id, name, qt_id, version, name))
    if ret:
        return ret[0][0]

    return False


def get_q_att(qt_id, name, variation, version=1000000000):
    """ Fetch an attachment for the question"""

    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    assert isinstance(variation, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    if version == 1000000000:
        version = get_qt_version(qt_id)
    if not version or not qt_id:
        L.warn("Request for unknown qt version. get_qt_att(%s, %s, %s, %s)" % (qt_id, name, variation, version))
        return None

    ret = run_sql("""SELECT qtemplate, data
                        FROM qattach
                        WHERE qtemplate=%s
                        AND name=%s
                        AND variation=%s
                        AND version=%s;""",
                  (qt_id, name, variation, version))
    if ret:
        data = str(ret[0][1])
        return data
    return get_qt_att(qt_id, name, version)


def get_qt_att(qt_id, name, version=1000000000):
    """ Fetch an attachment for the question template.
        If version is set to 0, will fetch the newest.
    """
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    if version == 1000000000:
        version = get_qt_version(qt_id)

    ret = run_sql("""SELECT data
                     FROM qtattach
                     WHERE qtemplate = %s
                       AND name = %s
                       AND version =
                         (SELECT MAX(version)
                          FROM qtattach
                          WHERE qtemplate=%s
                            AND version <= %s
                            AND name=%s);""",
                  (qt_id, name, qt_id, version, name))
    if ret:
        data = str(ret[0][0])

        return data

    return False


def get_exam_qts_in_pos(exam_id, position):
    """ Return the question templates in the given position in the exam, or 0.
    """
    assert isinstance(exam_id, int)
    assert isinstance(position, int)
    ret = run_sql("""SELECT qtemplate
                     FROM examqtemplates
                     WHERE exam=%s
                       AND position=%s;""", (exam_id, position))
    if ret:
        qtemplates = [int(row[0]) for row in ret]
        return qtemplates
    return []


def get_qt_exam_pos(exam_id, qt_id):
    """Return the position a given question template holds in the exam"""
    assert isinstance(exam_id, int)
    assert isinstance(qt_id, int)
    ret = run_sql("""SELECT position
                     FROM examqtemplates
                     WHERE exam=%s
                       AND qtemplate=%s;""", (exam_id, qt_id))
    if ret:
        return int(ret[0][0])
    return None


def get_topic_for_qtemplate(qt_id):
    """
    Find which topic a given qtemplate appears in.
    :param qt_id: (int) qtemplate
    :return: (int) topic_id or 0
    """
    # A question template should only be in one topic, but originally OASIS allowed
    # it to be in multiple topics, so just return the first.
    assert isinstance(qt_id, int)
    ret = run_sql("""SELECT topic
                     FROM questiontopics
                     WHERE qtemplate=%s LIMIT 1;""", (qt_id,))
    if ret:
        return int(ret[0][0])
    return 0


def get_qtemplate_practice_pos(qt_id):
    """ Fetch the position of a question template in a topic. """
    assert isinstance(qt_id, int)

    topic_id = get_topic_for_qtemplate(qt_id)
    key = "topic-%d-qtemplate-%d-position" % (topic_id, qt_id)
    obj = MC.get(key)
    if obj is not None:
        return int(obj)

    ret = run_sql("""SELECT position
                     FROM questiontopics
                     WHERE qtemplate=%s;""", (qt_id,))
    if ret:
        MC.set(key, ret[0][0], 120)  # remember for 2 minutes
        return int(ret[0][0])

    # if it hasn't been assigned a position, it's 0
    return 0


def get_qtemplates_in_topic_position(topic_id, position):
    """ Fetch a list of question template IDs in a given position in the topic. """
    assert isinstance(topic_id, int)
    assert isinstance(position, int)

    ret = run_sql("""SELECT qtemplate
                     FROM questiontopics
                     WHERE position=%s AND topic=%s;""", (position, topic_id))
    if ret:
        qtemplates = [row[0] for row in ret]
        return qtemplates
    return []


def get_qt_max_pos_in_topic(topic_id):
    """ Fetch the maximum position of a question template in a topic."""
    assert isinstance(topic_id, int)
    res = run_sql("""SELECT MAX(position)
                     FROM questiontopics
                     WHERE topic=%s;""", (topic_id,))
    if not res:
        return 0
    return res[0][0]


def get_qt_variations(qt_id, version=1000000000):
    """ Return all variations of a question template."""
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    if version == 1000000000:
        version = get_qt_version(qt_id)
    ret = {}
    res = run_sql("""SELECT variation, data
                     FROM qtvariations
                     WHERE qtemplate=%s
                       AND version =
                         (SELECT MAX(version)
                          FROM qtvariations
                          WHERE qtemplate=%s
                            AND version <= %s)""", (qt_id, qt_id, version))
    if not res:
        L.warn("No Variation found for qtid=%d, version=%d" % (qt_id, version))
        return []
    for row in res:
        result = str(row[1])
        ret[row[0]] = cPickle.loads(result)
    return ret


def get_qt_variation(qt_id, variation, version=1000000000):
    """ Return a specific variation of a question template."""
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    assert isinstance(variation, int)
    if version == 1000000000:
        version = get_qt_version(qt_id)
    res = run_sql("""SELECT data
                     FROM qtvariations
                     WHERE qtemplate=%s
                       AND variation=%s
                       AND version =
                         (SELECT MAX(version)
                          FROM qtvariations
                          WHERE qtemplate=%s
                            AND version <= %s);""",
                  (qt_id, variation, qt_id, version))
    if not res:
        L.warn("Request for unknown qt variation. (%s, %s, %s)" %
            (qt_id, variation, version))
        return None
    result = None
    data = None
    try:
        result = str(res[0][0])
        data = cPickle.loads(result)
    except TypeError:
        L.warn("Type error trying to cpickle.loads(%s) for (%s, %s, %s)" %
            (type(result), qt_id, variation, version))
    return data


def get_qt_num_variations(qt_id, version=1000000000):
    """ Return the number of variations for a question template. """
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    if version == 1000000000:
        version = get_qt_version(qt_id)
    ret = run_sql("""SELECT MAX(variation) FROM qtvariations
                        WHERE qtemplate=%s AND version = (
                         SELECT MAX(version) FROM qtvariations
                             WHERE qtemplate=%s AND version <= %s)""",
                  (qt_id, qt_id, int(version)))
    try:
        num = int(ret[0][0])
    except BaseException as err:
        L.warn("No Variation found for qtid=%d, version=%d: %s" %
            (qt_id, version, err))
        return 0
    return num


def create_q_att(qt_id, variation, name, mimetype, data, version):
    """ Create a new Question Attachment using given data."""
    assert isinstance(qt_id, int)
    assert isinstance(variation, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    assert isinstance(mimetype, str) or isinstance(mimetype, unicode)
    assert isinstance(data, str) or isinstance(data, unicode)
    assert isinstance(version, int)
    if not name and not data:
        L.warn("Refusing to create empty attachment for question %s" % qt_id)
        return
    safe_data = psycopg2.Binary(data)
    run_sql("""INSERT INTO qattach (qtemplate, variation, mimetype, name, data, version)
               VALUES (%s, %s, %s, %s, %s, %s);""",
               (qt_id, variation, mimetype, name, safe_data, version))


def create_qt_att(qt_id, name, mime_type, data, version):
    """ Create a new Question Template Attachment using given data."""
    assert isinstance(qt_id, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    assert isinstance(mime_type, str) or isinstance(mime_type, unicode)
    assert isinstance(data, str) or isinstance(data, unicode)
    assert isinstance(version, int)
    key = "qtemplateattach/%d/%s/%d" % (qt_id, name, version)
    MC.delete(key)
    if not data:
        data = ""
    L.info("QT Attachment upload '%s' '%s' %s bytes" % (name, mime_type, len(data)))
    if isinstance(data, unicode):
        data = data.encode("utf8")
    safe_data = psycopg2.Binary(data)
    run_sql("""INSERT INTO qtattach (qtemplate, mimetype, name, data, version)
               VALUES (%s, %s, %s, %s, %s);""",
            (qt_id, mime_type, name, safe_data, version))
    return None


def create_q(qt_id, name, student, status, variation, version, exam):
    """ Add a question (instance) to the database."""
    assert isinstance(qt_id, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    assert isinstance(student, int)
    assert isinstance(status, int)
    assert isinstance(variation, int)
    assert isinstance(version, int)
    assert isinstance(exam, int)
    res = run_sql("""INSERT INTO questions (qtemplate, name, student, status, variation, version, exam)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING question;""",
                  (qt_id, name, student, status, variation, version, exam))
    if not res:
        L.error("CreateQuestion(%d, %s, %d, %s, %d, %d, %d) may have failed." % (
                qt_id, name, student, status, variation, version, exam))
        return None
    return res[0][0]


def update_qt_title(qt_id, title):
    """ Update the title of a question template. """
    assert isinstance(qt_id, int)
    assert isinstance(title, str) or isinstance(title, unicode)
    key = "qtemplate-%d-name" % qt_id
    MC.delete(key)
    sql = "UPDATE qtemplates SET title = %s WHERE qtemplate = %s;"
    params = (title, qt_id)
    run_sql(sql, params)


def update_qt_owner(qt_id, owner):
    """ Update the owner of a question template.
        Generally we say the owner is the last person to alter the qtemplate.
    """
    assert isinstance(qt_id, int)
    assert isinstance(owner, int)
    key = "qtemplate-%d-owner" % qt_id
    MC.delete(key)
    sql = "UPDATE qtemplates SET owner = %s WHERE qtemplate = %s;"
    params = (owner, qt_id)
    run_sql(sql, params)


def update_qt_maxscore(qt_id, scoremax):
    """ Update the maximum score of a question template. """
    assert isinstance(qt_id, int)
    assert isinstance(scoremax, float) or scoremax is None
    key = "qtemplate-%d-maxscore" % qt_id
    MC.delete(key)
    sql = """UPDATE qtemplates SET scoremax=%s WHERE qtemplate=%s;"""
    params = (scoremax, qt_id)
    run_sql(sql, params)


def update_qt_marker(qt_id, marker):
    """ Update the marker of a question template."""
    assert isinstance(qt_id, int)
    assert isinstance(marker, int)
    sql = """UPDATE qtemplates
             SET marker=%s
             WHERE qtemplate=%s;"""
    params = (marker, qt_id)
    run_sql(sql, params)


def update_exam_qt_in_pos(exam_id, position, qts):
    """ Set the qtemplates at a given position in the exam to match
        the passed list. If we get qtlist = [0], we remove that position.
    """
    assert isinstance(exam_id, int)
    assert isinstance(position, int)
    assert isinstance(qts, list)
    # First remove the current set
    run_sql("DELETE FROM examqtemplates "
            "WHERE exam=%s "
            "AND position=%s;", (exam_id, position))
    # Now insert the new set
    for alt in qts:
        if alt > 0:
            if isinstance(alt, int):  # might be '---'
                run_sql("""INSERT INTO examqtemplates
                                (exam, position, qtemplate)
                           VALUES (%s, %s, %s);""",
                                (exam_id, position, alt))


def update_qt_practice_pos(qt_id, position):
    """ Update the position a question template holds in its topic."""
    assert isinstance(qt_id, int)
    assert isinstance(position, int)

    topic_id = get_topic_for_qtemplate(qt_id)
    move_qt_to_topic(qt_id, topic_id, position)


def move_qt_to_topic(qt_id, topic_id, position=None):
    """ Move a question template to a different sub category."""
    assert isinstance(qt_id, int)
    assert isinstance(topic_id, int)

    # clear out cached info about destination topic
    key = "topic-%d-qtemplate-%d-position" % (topic_id, qt_id)
    MC.delete(key)
    key = "topic-%d-numquestions" % topic_id
    MC.delete(key)
    key = "topic-%d-qtemplates" % topic_id
    MC.delete(key)

    # If we were in a different topic, clear out cached info about that
    prev_topic_id = get_topic_for_qtemplate(qt_id)
    if prev_topic_id:
        prev_position = get_qtemplate_practice_pos(qt_id)
        if position is None:
            position = prev_position
        key = "topic-%d-qtemplate-%d-position" % (prev_topic_id, qt_id)
        MC.delete(key)
        key = "topic-%d-numquestions" % prev_topic_id
        MC.delete(key)
        key = "topic-%d-qtemplates" % prev_topic_id
        MC.delete(key)

        run_sql("""UPDATE questiontopics SET "topic"=%s, "position"=%s WHERE "qtemplate"=%s;""", (topic_id, position, qt_id))
    else:
        if position is None:
            position = 0
        run_sql("""INSERT INTO questiontopics ("qtemplate", "topic", "position")
                VALUES (%s, %s, %s)""", (qt_id, topic_id, position))


def copy_qt_all(qt_id):
    """ Make an identical copy of a question template,
        including all attachments.
    """
    assert isinstance(qt_id, int)
    newid = _copy_qt(qt_id)
    if newid <= 0:
        return 0
    attachments = get_qt_atts(qt_id)
    newversion = get_qt_version(newid)
    for name in attachments:
        create_qt_att(newid,
                      name,
                      get_qt_att_mimetype(qt_id, name),
                      get_qt_att(qt_id, name),
                      newversion)
    try:
        variations = get_qt_variations(qt_id)
        for variation in variations.keys():
            add_qt_variation(newid,
                             variation,
                             variations[variation],
                             newversion)
    except AttributeError as err:
        L.warn("Copying a qtemplate %s with no variations. '%s'" % (qt_id, err))
    return newid


def _copy_qt(qt_id):
    """ Make an identical copy of a question template entry.
        Returns the new qtemplate id.
    """
    assert isinstance(qt_id, int)
    res = run_sql("SELECT owner, title, description, marker, scoremax, status "
                  "FROM qtemplates "
                  "WHERE qtemplate = %s",
                  (qt_id,))
    if not res:
        raise KeyError("QTemplate %d not found" % qt_id)
    orig = res[0]
    new_id = create_qt(
        owner=int(orig[0]),
        title=orig[1],
        desc=orig[2],
        marker=orig[3],
        score_max=orig[4],
        status=int(orig[5])
    )
    if new_id <= 0:
        raise IOError("Unable to create copy of QTemplate %d" % qt_id)
    return new_id


def add_qt_variation(qt_id, variation, data, version):
    """ Add a variation to the question template. """
    assert isinstance(qt_id, int)
    assert isinstance(variation, int)
    assert isinstance(version, int)
    pick = cPickle.dumps(data)
    safe_data = psycopg2.Binary(pick)
    run_sql("INSERT INTO qtvariations (qtemplate, variation, data, version) "
            "VALUES (%s, %s, %s, %s)",
            (qt_id, variation, safe_data, version))


def create_qt(owner, title, desc, marker, score_max, status, topic_id=None):
    """ Create a new Question Template. """
    assert isinstance(owner, int)
    assert isinstance(title, str) or isinstance(title, unicode)
    assert isinstance(desc, str) or isinstance(desc, unicode)
    assert isinstance(marker, int)
    assert isinstance(score_max, float) or score_max is None
    assert isinstance(status, int)
    assert isinstance(topic_id, int) or topic_id is None

    L.debug("Creating question template %s (owner %s)" % (title, owner))
    res = run_sql("INSERT INTO qtemplates (owner, title, description, marker, scoremax, status, version) "
                  "VALUES (%s, %s, %s, %s, %s, %s, 2) RETURNING qtemplate;",
                  (owner, title, desc, marker, score_max, status))
    qt_id = None
    if res:
        qt_id = int(res[0][0])

    if topic_id and qt_id:
        move_qt_to_topic(qt_id, topic_id,0)
    if qt_id:
        return qt_id
    L.error("create_qt error (%d, %s, %s, %d, %s, %s)" % (owner, title, desc, marker, score_max, status))


def _serialize_courseexaminfo(info):
    """ Serialize the structure for, eg. cache.
        The dates, especially, need work before JSON
    """
    fmt = '%Y-%m-%d %H:%M:%S'
    safe = {}
    for k, exam in info.iteritems():
        safe[k] = exam
        safe[k]['start'] = exam['start'].strftime(fmt)
        safe[k]['end'] = exam['end'].strftime(fmt)
    return json.dumps(safe)


def _deserialize_courseexaminfo(obj):
    """ Deserialize a serialized exam info structure."""
    fmt = '%Y-%m-%d %H:%M:%S'
    safe = json.loads(obj)
    info = {}
    for k, exam in safe.iteritems():
        info[k] = exam
        info[k]['start'] = datetime.datetime.strptime(exam['start'], fmt)
        info[k]['end'] = datetime.datetime.strptime(exam['end'], fmt)
    return info


def get_course_exam_all(course_id, prev_years=False):
    """ Return a summary of information about all current exams in the course
        {id, course, name, description, start, duration, end, type}
    """
    assert isinstance(course_id, int)
    assert isinstance(prev_years, bool)
    if prev_years:
        key = "course-exam-all-%s-prevyears" % course_id
    else:
        key = "course-exam-all-%s" % course_id
    obj = MC.get(key)
    if obj:
        return _deserialize_courseexaminfo(obj)

    if prev_years:
        sql = """SELECT exam, course, title, "type", "start", "end",
                    description, duration, to_char("start", 'DD Mon'),
                    to_char("start", 'hh:mm'), to_char("end", 'DD Mon'),
                    to_char("end", 'hh:mm')
                 FROM exams
                 WHERE course='%s' AND archived='0'
                 ORDER BY "start";"""
    else:
        sql = """SELECT exam, course, title, "type", "start", "end",
                    description, duration, to_char("start", 'DD Mon'),
                    to_char("start", 'hh:mm'), to_char("end", 'DD Mon'),
                    to_char("end", 'hh:mm')
                 FROM exams
                 WHERE course='%s'
                 AND archived='0'
                 AND extract('year' from "end") = extract('year' from now())
                 ORDER BY "start";"""
    params = (course_id,)
    ret = run_sql(sql, params)
    info = {}
    if ret:
        for row in ret:
            info[int(row[0])] = {'id': row[0], 'course': row[1], 'name': row[2],
                                 'type': row[3], 'start': row[4], 'end': row[5],
                                 'description': row[6], 'duration': row[7],
                                 'startdate': row[8], 'starttime': row[9],
                                 'enddate': row[10], 'endtime': row[11]}
    # 60 second cache. take the edge off an exam start peak load
    MC.set(key, _serialize_courseexaminfo(info), 60)

    return info


def add_exam_q(user, exam, question, position):
    """Record that the student was assigned the given question for assessment.
    """
    assert isinstance(user, int)
    assert isinstance(exam, int)
    assert isinstance(question, int)
    assert isinstance(position, int)
    L.debug("Assigning question %s to user %s for exam %s, position %s" % (question, user, exam, position))
    sql = """SELECT id FROM examquestions
              WHERE exam = %s
              AND student = %s
              AND position = %s
              AND question = %s;"""
    params = (exam, user, position, question)
    ret = run_sql(sql, params)
    if ret:  # already exists
        return
    run_sql("INSERT INTO examquestions (exam, student, position, question) "
            "VALUES (%s, %s, %s, %s);",
            (exam, user, position, question))
    touch_user_exam(exam, user)


def get_student_q_practice_num(user_id, qt_id):
    """Return the number of times the given student has practiced the question
       Exclude assessed scores.
    """
    assert isinstance(user_id, int)
    assert isinstance(qt_id, int)
    sql = """SELECT
                 COUNT(question)
             FROM
                 questions
             WHERE
                    qtemplate=%s
                 AND
                    student=%s
                 AND
                    status > 1
                 AND
                    exam < 1
              GROUP BY qtemplate;
              """
    params = (qt_id, user_id)

    ret = run_sql(sql, params)
    if ret:
        i = ret[0]
        num = int(i[0])
        return num
    else:
        return 0


def secs_to_human(seconds):
    """Convert a number of seconds to a human readable string, eg  "8 days"
    """
    assert isinstance(seconds, int) or isinstance(seconds, float)
    return "%d days ago" % int(seconds / 86400)


def get_prac_stats_user_qt(user_id, qt_id):
    """ Return Data on the scores of individual practices. it is used to
        display Individual Practise Data section
        Restricted by a certain time period which is 30 secs to 2 hours"""
    assert isinstance(user_id, int)
    assert isinstance(qt_id, int)
    sql = """SELECT COUNT(question),MAX(score),MIN(score),AVG(score)
             FROM questions WHERE qtemplate = %s AND student = %s;"""
    params = (qt_id, user_id)
    ret = run_sql(sql, params)
    if ret:
        i = ret[0]
        if i[0]:
            stats = {'num': int(i[0]),
                     'max': float(i[1]),
                     'min': float(i[2]),
                     'avg': float(i[3])}
            return stats
    return None


def get_student_q_practice_stats(user_id, qt_id, num=3):
    """Return data on the scores obtained while practicing the given question
       the last 'num' times. Exclude assessed scores. If num is not provided,
       defaults to 3. If num is 0, give stats for all.
       Returns list of last 'num' practices:
       {'score': score, 'question':question id, 'age': seconds since practiced }
       New Changes: set up a time period.
       It only shows the stats within 30 secs to 2 hrs.
    """
    assert isinstance(user_id, int)
    assert isinstance(qt_id, int)
    assert isinstance(num, int)
    sql = """SELECT
                 score, question, EXTRACT(epoch FROM (NOW() - marktime))
             FROM questions
             WHERE qtemplate=%s
                 AND student=%s
                 AND status > 1
                 AND exam < 1
                 AND marktime > '2005-07-16 00:00:00.00'
                 AND (marktime - firstview) > '00:00:20.00'
                 AND (marktime - firstview) < '02:00:01.00'
             ORDER BY marktime DESC"""
    params = (qt_id, user_id)
    if num > 0:
        sql += " LIMIT '%d'" % num
    sql += ";"
    ret = run_sql(sql, params)
    stats = []
    if ret:
        for row in ret:
            ageseconds = 10000000000  # could be from before we tracked it.
            age = row[2]
            try:
                age = int(age)
                ageseconds = age
                if age > 63000000:    # more than two years
                    age = "more than 2 years"
                else:
                    age = secs_to_human(age)
            except (TypeError, ValueError):
                age = "more than 2 years"
            stats.append({
                'score': float(row[0]),
                'question': int(row[1]),
                'age': age,
                'ageseconds': ageseconds
            })

        return stats[::-1]   # reverse it so they're in time order
    return None


def get_q_stats_class(course, qt_id):
    """Fetch a bunch of statistics about the given question for the class
    """
    assert isinstance(course, int)
    assert isinstance(qt_id, int)
    sql = """SELECT COUNT(question),
                    AVG(score),
                    STDDEV(score),
                    MAX(score),
                    MIN(score)
             FROM questions
             WHERE qtemplate = %s
             AND marktime < NOW()
             AND (marktime - firstview) > '00:00:20'
             AND (marktime - firstview) < '02:00:01'
             AND student IN
                (SELECT userid FROM usergroups WHERE groupid IN
                  (SELECT groupid FROM groupcourses WHERE course = %s)
             );
          """
    params = (qt_id, course)
    ret = run_sql(sql, params)
    if ret:
        i = ret[0]
        if i[1]:
            if i[2]:
                stats = {'count': int(i[0]),
                         'avg': float(i[1]),
                         'stddev': float(i[2]),
                         'max': float(i[3]),
                         'min': float(i[4])}
            else:   # empty stddev from e.g. only 1 count
                stats = {'count': int(i[0]),
                         'avg': float(i[1]),
                         'stddev': 0.0,
                         'max': float(i[3]),
                         'min': float(i[4])}
            return stats


def set_message(name, message):
    """Store a message
    """
    assert isinstance(name, str) or isinstance(name, unicode)
    assert isinstance(message, str) or isinstance(message, unicode)

    ret = run_sql("SELECT COUNT(message) FROM messages WHERE name=%s;",
                  (name,))
    if ret and len(ret) and int(ret[0][0]) >= 1:
        run_sql("UPDATE messages SET message=%s WHERE name=%s;",
                (message, name))
        L.info("Message %s updated to %s." % (name, message))
    else:
        run_sql("INSERT INTO messages (name, message) VALUES (%s, %s);",
                (name, message))
        L.info("Message %s inserted as %s." % (name, message))


def get_message(name):
    # type: (str) -> str
    """Retrieve a message
    """
    assert isinstance(name, str) or isinstance(name, unicode)

    ret = run_sql("SELECT message FROM messages WHERE name=%s;",
                  (name,))
    if not ret:
        return ""
    return ret[0][0]


def touch_user_exam(exam_id, user_id):
    """ Update the lastchange field on a user exam so other places can tell that
        something changed. This should probably be done any time one of the
        following changes:
            userexam fields on that row
            question/guess in the exam changes
    """
    assert isinstance(exam_id, int)
    assert isinstance(user_id, int)
    sql = "UPDATE userexams SET lastchange=NOW() WHERE exam=%s AND student=%s;"
    params = (exam_id, user_id)
    run_sql(sql, params)


def get_qt_editor(qt_id):
    """ Return which type of editor the question should use.
        OQE | Raw | QE2
    """
    assert isinstance(qt_id, int)
    atts = get_qt_atts(qt_id)
    for att in atts:
        if att.endswith(".qe2"):
            return "qe2"
        if att.endswith(".oqe"):
            return "OQE"
    return "Raw"


def get_db_version():
    """ Return an string representing the database version
        If it's too old to have a configuration field, then use some heuristics.
    """

    # We have a setting, easy
    try:
        ret = run_sql("""SELECT "value"
                         FROM config
                         WHERE "name" = 'dbversion';""", quiet=True)
        if ret:
            return ret[0][0]
    except psycopg2.DatabaseError:
        pass

    # We don't have a setting, need to figure it out
    try:  # questionflags was removed for 3.9.1
        ret = run_sql("SELECT 1 FROM questionflags;", quiet=True)
        if isinstance(ret, list):
            return "3.6"

    except psycopg2.DatabaseError:
        pass

    try:  # one of the very original fields
        ret = run_sql("""SELECT 1 from users;""")
        if ret:
            return "3.9.1"
    except psycopg2.DatabaseError:
        pass

    # No database at all?
    return "unknown"


def get_db_size():
    """ Find out how much space the DB is taking
        Return as a list of  [  [tablename, size] , ... ]
    """

    # Query from   http://wiki.postgresql.org/wiki/Disk_Usage
    sql = """SELECT nspname || '.' || relname AS "relation",
                    pg_size_pretty(pg_total_relation_size(C.oid)) AS "total_size"
             FROM pg_class C
             LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
             WHERE nspname NOT IN ('pg_catalog', 'information_schema')
               AND C.relkind <> 'i'
               AND nspname !~ '^pg_toast'
             ORDER BY pg_total_relation_size(C.oid) DESC
             LIMIT 10;
    """

    ret = run_sql(sql)
    sizes = []
    for row in ret:
        sizes.append([row[0], row[1]])

    return sizes


def check_safe():
    """ Is it safe to do dangerous stuff to the database? Mainly tries to
        figure out if there is real data in it.
    """
    # If there are only 2 or fewer user accounts and questions, assume it's
    # ok.

    what = is_oasis_db()
    if what == "no":
        return False

    if what == "empty":
        return True

    users = num_records("users")
    print '%s user records' % users
    qtemplates = num_records("qtemplates")
    print '%s question templates' % qtemplates
    exams = num_records("exams")
    print '%s assessments' % exams

    if users > 2:
        print "Contains non-default data."
        return False

    if qtemplates > 1:
        print "Contains non-default data."
        return False

    if exams > 0:
        print "Contains non-default data."
        return False

    return True


def is_oasis_db():
    """ Is this likely an OASIS database? Look at the table names to see
        if we have the more specific ones.
        Return "yes", "no", or "empty"
    """

    expect = ['qtvariations', 'users', 'examqtemplates', 'marklog', 'qtattach',
              'questions', 'guesses', 'exams', 'qtemplates']

    tables = public_tables()

    if len(tables) == 0:
        return "empty"

    if set(expect).issubset(tables):
        return "yes"

    return "no"


def public_tables():
    """ Return a list of names of all tables in schema ("public" is default)
    """

    ret = run_sql("SELECT * FROM pg_stat_user_tables;")
    tables = [row[2] for row in ret]
    return tables


def num_records(table_name):
    """ How many rows are in the given table.
    """
    ret = run_sql('SELECT count(*) FROM "%s";' % table_name)
    num = int(ret[0][0])
    return num


def erase_existing():
    """ Remove the existing database. DANGEROUS
    """

    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "eraseexisting.sql")) as f:
        sql = f.read()
    print "Removing existing tables."
    run_sql(sql)


def clean_install_3_6():
    """ Install a fresh blank v3.6 schema.
    """

    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "emptyschema_36x.sql")) as f:
        sql = f.read()

    run_sql(sql)
    print "Installed v3.6.x table structure."


def clean_install_3_9_1():
    """ Install a fresh blank v3.9.1 schema.
    """

    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "emptyschema_391.sql")) as f:
        sql = f.read()

    run_sql(sql)
    print "Installed v3.9.1 table structure."


def clean_install_3_9_2():
    """ Install a fresh blank v3.9.2 schema.
    """

    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "emptyschema_392.sql")) as f:
        sql = f.read()

    run_sql(sql)
    print "Installed v3.9.2 table structure."


def clean_install_3_9_3():
    """ Install a fresh blank v3.9.3 schema.
    """

    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "emptyschema_393.sql")) as f:
        sql = f.read()

    run_sql(sql)
    print "Installed v3.9.3 table structure."


def clean_install_3_9_4():
    """ Install a fresh blank v3.9.4 schema.
    """

    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "emptyschema_394.sql")) as f:
        sql = f.read()

    run_sql(sql)
    print "Installed v3.9.4 table structure."


def clean_install_3_9_5():
    """ Install a fresh blank v3.9.4 schema.
    """
    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "emptyschema_395.sql")) as f:
        sql = f.read()

    run_sql(sql)
    print "Installed v3.9.5 table structure."


def upgrade_3_6_to_3_9_5(options):
    """ Given a 3.6 database, upgrade it to 3.9.3
    """
    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_36x_to_392.sql")) as f:
        sql = f.read()

    run_sql(sql)
    print "Migrated table structure from 3.6 to 3.9.2"

    calc_stats()

    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_392_to_393.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.2 to 3.9.3"

    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_393_to_394.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.3 to 3.9.4"
    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_394_to_395.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.4 to 3.9.5"

    if not options.noresetadmin:
        generate_admin_passwd()  # 3.6 passwords were in a slightly less secure format


def upgrade_3_9_1_to_3_9_5(options):
    """ Given a 3.9.1 database, upgrade it to 3.9.4.
    """
    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_391_to_392.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.1 to 3.9.2"

    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_392_to_393.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.2 to 3.9.3"

    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_393_to_394.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.3 to 3.9.4"
    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_394_to_395.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.4 to 3.9.5"


def upgrade_3_9_2_to_3_9_5(options):
    """ Given a 3.9.2 database, upgrade it to 3.9.4.
    """
    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_392_to_393.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.2 to 3.9.3"

    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_393_to_394.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.3 to 3.9.4"
    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_394_to_395.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.4 to 3.9.5"


def upgrade_3_9_3_to_3_9_5(options):
    """ Given a 3.9.3 database, upgrade it to 3.9.5.
    """
    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_393_to_394.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.3 to 3.9.4"
    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_394_to_395.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.4 to 3.9.5"


def upgrade_3_9_4_to_3_9_5(options):
    """ Given a 3.9.4 database, upgrade it to 3.9.5.
    """
    with open(os.path.join(os.path.dirname(OaConfig.homedir), "deploy", "migrate_394_to_395.sql")) as f:
        sql = f.read()
    run_sql(sql)
    print "Migrated table structure from 3.9.4 to 3.9.5"


def do_upgrade(options):
    """ Upgrade the database from an older version of OASIS.
    """

    dbver = get_db_version()
    if dbver == "3.6":
        upgrade_3_6_to_3_9_5(options)
        return
    if dbver == "3.9.1":
        upgrade_3_9_1_to_3_9_5(options)
        return
    if dbver == "3.9.2":
        upgrade_3_9_2_to_3_9_5(options)
        return
    if dbver == "3.9.3":
        upgrade_3_9_3_to_3_9_5(options)
        return
    if dbver == "3.9.4":
        upgrade_3_9_4_to_3_9_5(options)
        return
    if dbver == "3.9.5":
        print "Your database is already the latest version (3.9.5)"
    return


def generate_admin_passwd():
    """ Generate a new random password for the admin account.
    """
    from oasis.lib import Users, Users2, Permissions

    ver = get_db_version()

    passwd = Users.gen_confirm_code()

    uid = Users.uid_by_uname('admin')
    if not uid:
        if ver == "3.6":
            sql = """
                INSERT INTO users (uname, passwd, givenname, familyname,
                                  acctstatus, student_id, email, expiry,
                                  source)
                VALUES ('admin', 'NOLOGIN', 'Admin', 'Account',
                        1, '', '', NULL,
                        'local');
                """
            run_sql(sql)
            uid = Users.uid_by_uname('admin')
        else:
            uid = Users.create(
                uname="admin",
                passwd="NOLOGIN",
                email=OaConfig.email,
                givenname="Admin",
                familyname="Account",
                acctstatus=1,
                studentid="",
                source="local",
                confirm_code="",
                confirm=True)

    Users2.set_password(uid, passwd)

    Permissions.add_perm(uid, 0, 1)  # superuser
    L.warn("Admin password reset")
    print "Admin password reset to: ", passwd
    return passwd


def calc_stats():
    """ Run stats generation over the whole database.
    """
    print "Calculating Statistics"
    from oasis.lib import Stats
    Stats.do_initial_stats_update()


