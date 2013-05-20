# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" OaDB.py
    This provides a collection of methods for accessing the database.
    If the database is changed to something other than postgres, this
    is where to start. Since this has grown so large, parts of it are
    being broken off and put in db/*.py
"""

import psycopg2
import cPickle
import datetime
import json

from logging import log, INFO, WARN, ERROR

# Global dbpool
import OaConfig
import OaPool

dbpool = OaPool.DbPool(OaConfig.oasisdbconnectstring, 3)  # 3 connections. This lets us keep going if one is slow but
                                                          # doesn't overload the server if there're a lot of us

# Cache stuff on local drives to save our poor database
fileCache = OaPool.fileCache(OaConfig.cachedir)

from OaPool import MCPool

# Get a pool of memcache connections to use
MC = MCPool('127.0.0.1:11211', 3)


def run_sql(sql, params=None):
    """ Execute SQL commands using the dbpool"""
    conn = dbpool.begin()
    res = conn.run_sql(sql, params)
    dbpool.commit(conn)
    return res


def setQuestionViewTime(question):
    """ Record that the question has been viewed.
        Not a good idea to call multiple times since it's
        nearly always the first time that we want.
    """
    assert isinstance(question, int)
    run_sql("UPDATE questions SET firstview=NOW() WHERE question=%s;", (question,))


def setQuestionMarkTime(question):
    """ Record that the question was marked.
        Probably best not to call multiple times since
        we usually want the first time.
    """
    assert isinstance(question, int)
    run_sql("UPDATE questions SET marktime=NOW() WHERE question=%s;", (question,))


def getQuestionViewTime(question):
    """ Return the time that the question was first viewed
        as a human readable string.
    """
    assert isinstance(question, int)
    ret = run_sql("""SELECT firstview FROM questions WHERE question=%s;""", (question,))
    if ret:
        firstview = ret[0][0]
        if firstview:
            return firstview.strftime("%Y %b %d, %I:%M%P")
    return None


def getQuestionMarkTime(question):
    """ Return the time that the question was marked
        as a human readable string, or None if it hasn't been.
    """
    assert isinstance(question, int)
    ret = run_sql("""SELECT marktime FROM questions WHERE question=%s;""", (question,))
    if ret:
        marktime = ret[0][0]
        if marktime:
            return marktime.strftime("%Y %b %d, %I:%M%P")
    return None


def getAllQTemplates():
    """ Return a list of all qtemplates in the system (no matter what the status """
    ret = run_sql("SELECT qtemplate FROM qtemplates ORDER BY qtemplate;")
    qtemplates = []
    if ret:
        for row in ret:
            qtemplates.append(row[0])
    return qtemplates


def getExamQuestionByPositionStudent(exam, position, student):
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


def getExamQuestionByQTStudent(exam, qt_id, student):
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


def getQuestionByQTStudent(qt_id, student):
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


def updateQuestionScore(q_id, score):
    """ Set the score of a question."""
    assert isinstance(q_id, int)
    try:
        sc = float(score)
    except (TypeError, ValueError):
        log(ERROR, "Unable to cast score to float!? '%s'" % score)
        return
    run_sql("""UPDATE questions SET score=%s WHERE question=%s;""", ("%.1f" % sc, q_id))


def setQuestionStatus(q_id, status):
    """ Set the status of a question."""
    assert isinstance(q_id, int)
    assert isinstance(status, int)
    run_sql("""UPDATE questions SET status=%s WHERE question=%s;""", (status, q_id))


def getQuestionVersion(q_id):
    """ Return the template version this question was generated from """
    assert isinstance(q_id, int)
    ret = run_sql("""SELECT version FROM questions WHERE question=%s;""", (q_id,))
    if ret:
        return int(ret[0][0])
    return None


def getQuestionScore(q_id):
    """ Return the score obtained on this question """
    assert isinstance(q_id, int)
    ret = run_sql("""SELECT score FROM questions WHERE question=%s;""", (q_id,))
    if ret:
        return float(ret[0][0])
    return None


def getQuestionVariation(q_id):
    """ Return the template variation this question was generated from"""
    assert isinstance(q_id, int)
    ret = run_sql("""SELECT variation FROM questions WHERE question=%s;""", (q_id,))
    if ret:
        return int(ret[0][0])
    return None


def getQuestionParent(q_id):
    """ Return the template this question was generated from"""
    assert isinstance(q_id, int)
    ret = run_sql("""SELECT qtemplate FROM questions WHERE question=%s;""", (q_id,))
    if ret:
        return int(ret[0][0])
    log(ERROR, "No parent found for question %s!" % q_id)
    return None


def saveGuess(q_id, part, value):
    """ Store the guess in the database."""
    assert isinstance(q_id, int)
    assert isinstance(part, int)
    assert isinstance(value, unicode)
    # noinspection PyComparisonWithNone
    if not value is None:  # "" is legit
        run_sql("INSERT INTO guesses (question, created, part, guess) VALUES (%s, NOW(), %s, %s);", (q_id, part, value))


def getQuestionGuesses(q_id):
    """ Return a dictionary of the recent guesses in a question."""
    assert isinstance(q_id, int)
    ret = run_sql("SELECT part, guess FROM guesses WHERE question = %s ORDER BY created DESC;", (q_id,))
    if not ret:
        return {}
    guesses = {}
    for row in ret:
        if not "G%d" % (int(row[0])) in guesses:
            guesses["G%d" % (int(row[0]))] = row[1]
    return guesses


def getQuestionGuessesBeforeTime(q_id, lasttime):
    """ Return a dictionary of the recent guesses in a question, from before it was marked. """
    assert isinstance(q_id, int)
    assert isinstance(lasttime, datetime.datetime)
    ret = run_sql("SELECT part, guess FROM guesses WHERE question=%s AND created < %s ORDER BY created DESC;",
                  (q_id, lasttime))
    if not ret:
        return {}
    guesses = {}
    for row in ret:
        if not "G%d" % (int(row[0])) in guesses:
            guesses["G%d" % (int(row[0]))] = row[1]
    return guesses


def getQTemplatesInTopic(topic_id):
    """ Return a list of the QTemplates in the given Topic. """
    assert isinstance(topic_id, int)
    key = "topic-%d-qtemplates" % topic_id
    obj = MC.get(key)
    if obj:
        return list(obj)
    sql = """select qtemplates.qtemplate
            from questiontopics,qtemplates
            where questiontopics.topic=%s
            and questiontopics.qtemplate = qtemplates.qtemplate;"""
    params = (topic_id,)
    ret = run_sql(sql, params)
    qtemplates = []
    if ret:
        qtemplates = [int(row[0]) for row in ret]
        MC.set(key, qtemplates, 120)
    return qtemplates


def getQTemplateByEmbedID(embed_id):
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


def getQTemplate(qt_id, version=None):
    """ Return a dictionary with the QTemplate information """
    assert isinstance(qt_id, int)
    assert isinstance(version, int) or version is None
    if version:
        sql = """SELECT qtemplate, owner, title, description, marker, scoremax, version, status, embed_id
                    FROM qtemplates WHERE qtemplate=%s and version=%s;"""
        params = (qt_id, version)
    else:
        sql = """SELECT qtemplate, owner, title, description, marker, scoremax, version, status, embed_id
                    FROM qtemplates WHERE qtemplate=%s ORDER BY version DESC LIMIT 1;"""
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


def updateQTemplateEmbedID(qt_id, embed_id):
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


def incrementQTVersion(qt_id):
    """ Increase the version number of the current question template"""
    # FIXME: Not done in a parallel-safe manner. Could maybe find a way to do this
    # in the database. Fairly low risk.
    assert isinstance(qt_id, int)
    version = int(getQTVersion(qt_id))
    version += 1
    run_sql("""UPDATE qtemplates SET version=%s WHERE qtemplate=%s;""", (version, qt_id))
    return version


def getQTVersion(qt_id):
    """ Fetch the version of a question template."""
    assert isinstance(qt_id, int)
    ret = run_sql("""SELECT version FROM qtemplates WHERE qtemplate=%s;""", (qt_id,))
    if ret:
        return int(ret[0][0])
    log(WARN, "Request for unknown question template %s." % qt_id)


def getQTemplateMaxScore(qt_id):
    """ Fetch the maximum score of a question template."""
    assert isinstance(qt_id, int)
    key = "qtemplate-%d-maxscore" % (qt_id,)
    obj = MC.get(key)
    if not obj is None:  # 0 or [] or "" could be legit
        return obj
    ret = run_sql("""SELECT scoremax FROM qtemplates WHERE qtemplate=%s;""", (qt_id,))
    if ret:
        try:
            scoremax = float(ret[0][0])
        except (ValueError, TypeError, KeyError):
            scoremax = 0.0
        MC.set(key, scoremax)
        return scoremax
    log(WARN, "Request for unknown question template %s." % qt_id)


def getQTemplateMarker(qt_id):
    """ Fetch the marker of a question template."""
    assert isinstance(qt_id, int)
    ret = run_sql("""SELECT marker FROM qtemplates WHERE qtemplate=%s;""", (qt_id,))
    if ret:
        return int(ret[0][0])
    log(WARN, "Request for unknown question template %s." % qt_id)


def getQTemplateOwner(qt_id):
    """ Fetch the owner of a question template.
        (The last person to make changes to it)
    """
    assert isinstance(qt_id, int)
    ret = run_sql("""SELECT owner FROM qtemplates WHERE qtemplate=%s;""", (qt_id,))
    if ret:
        return ret[0][0]
    log(WARN, "Request for unknown question template %s." % qt_id)


def getQTemplateName(qt_id):
    """ Fetch the name of a question template."""
    assert isinstance(qt_id, int)
    key = "qtemplate-%d-name" % qt_id
    obj = MC.get(key)
    if not obj is None:
        return obj
    ret = run_sql("""SELECT title FROM qtemplates WHERE qtemplate=%s;""", (qt_id,))
    if ret:
        MC.set(key, ret[0][0], expiry=360)  # 6 minutes
        return ret[0][0]
    log(WARN, "Request for unknown question template %s." % qt_id)


def getQTemplateEmbedID(qt_id):
    """ Fetch the embed_id of a question template."""
    assert isinstance(qt_id, int)
    ret = run_sql("""SELECT embed_id FROM qtemplates WHERE qtemplate=%s;""", (qt_id,))
    if ret:
        embed_id = ret[0][0]
        if not embed_id:
            embed_id = ""
        return embed_id
    log(WARN, "Request for unknown question template %s." % qt_id)


def getQTAttachments(qt_id, version=1000000000):
    """ Return a list of (names of) all attachments connected to
        this question template.
    """
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    if version == 1000000000:
        version = getQTVersion(qt_id)
    attachments = []
    ret = run_sql("""SELECT name FROM qtattach WHERE qtemplate = %s AND version <= %s
                  GROUP BY name ORDER BY name;""", (qt_id, version))
    if ret:
        attachments = [attachment[0] for attachment in ret if attachment[0] not in attachments and attachment[0]]
        return attachments
    return []


def getQAttachmentMimeType(qt_id, name, variation, version=1000000000):
    """ Return a string containing the mime type of the attachment.
    """
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    assert isinstance(variation, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    if version == 1000000000:
        version = getQTVersion(qt_id)
    try:
        key = "questionattach/%d/%s/%d/%d/mimetype" % (qt_id, name, variation, version)
        (value, found) = fileCache.get(key)
        if not found:
            ret = run_sql("""SELECT qtemplate, mimetype
                                FROM qattach
                                WHERE name=%s
                                AND qtemplate=%s
                                AND variation=%s
                                AND version=%s
                                """, (name, qt_id, variation, version))
            if ret:
                data = ret[0][1]
                fileCache.set(key, data)
                return data
                # We use mimetype to see if an attachment is generated so not finding one is no big deal.
            return False
        return value
    except BaseException, err:
        log(WARN, "%s args=(%s,%s,%s,%s)" % (err, qt_id, name, variation, version))
    return False


def getQTAttachmentMimeType(qt_id, name, version=1000000000):
    """ Fetch the mime type of a template attachment.
        If version is set to 0, will fetch the newest.
    """
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    if version == 1000000000:
        version = getQTVersion(qt_id)
    key = "qtemplateattach/%d/%s/%d/mimetype" % (qt_id, name, version)
    (value, found) = fileCache.get(key)
    if not found:
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
            data = ret[0][0]
            fileCache.set(key, data)
            return data
        return False
    return value


def getQAttachmentFilename(qt_id, name, variation, version=1000000000):
    """ Fetch the on-disk filename where the attachment is stored.
        This may have to fetch it from the database.
        The intent is to save time by passing around a filename rather than the
        entire attachment.
    """
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    assert isinstance(variation, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    if version == 1000000000:
        version = getQTVersion(qt_id)
    key = "questionattach/%d/%s/%d/%d" % (qt_id, name, variation, version)
    (filename, found) = fileCache.getFilename(key)
    if not found:
        ret = run_sql("""SELECT qtemplate, data
                            FROM qattach
                            WHERE qtemplate=%s
                            AND name=%s
                            AND variation=%s
                            AND version=%s;""",
                      (qt_id, name, variation, version))
        if ret:
            data = str(ret[0][1])
            fileCache.set(key, data)
            (filename, found) = fileCache.getFilename(key)
            if found:
                return filename
        fileCache.set(key, False)
        return False
    return filename


def getQAttachment(qt_id, name, variation, version=1000000000):
    """ Fetch an attachment for the question"""
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    assert isinstance(variation, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    if version == 1000000000:
        version = getQTVersion(qt_id)
    key = "questionattach/%d/%s/%d/%d" % (qt_id, name, variation, version)
    (value, found) = fileCache.get(key)
    if not found:
        ret = run_sql("""SELECT qtemplate, data
                            FROM qattach
                            WHERE qtemplate=%s
                            AND name=%s
                            AND variation=%s
                            AND version=%s;""",
                      (qt_id, name, variation, version))
        if ret:
            data = str(ret[0][1])
            fileCache.set(key, data)
            return data
        fileCache.set(key, False)
        return getQTAttachment(qt_id, name, version)
    return value


def getQTAttachmentFilename(qt_id, name, version=1000000000):
    """ Fetch a filename for the attachment in the question template.
        If version is set to 0, will fetch the newest.
    """
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    if version == 1000000000:
        version = getQTVersion(qt_id)
    key = "qtemplateattach/%d/%s/%d" % (qt_id, name, version)
    (filename, found) = fileCache.getFilename(key)
    if (not found) or version == 1000000000:
        ret = run_sql("SELECT data FROM qtattach WHERE qtemplate = %s AND name = %s AND version = "
                      "  (SELECT MAX(version) FROM qtattach WHERE "
                      " qtemplate=%s AND version <= %s AND name=%s)", (qt_id, name, qt_id, version, name))
        if ret:
            data = str(ret[0][0])
            fileCache.set(key, data)
            (filename, found) = fileCache.getFilename(key)
            if found:
                return filename
        fileCache.set(key, False)
        return False
    return filename


def getQTAttachment(qt_id, name, version=1000000000):
    """ Fetch an attachment for the question template.
        If version is set to 0, will fetch the newest.
    """
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    if version == 1000000000:
        version = getQTVersion(qt_id)
    key = "qtemplateattach/%d/%s/%d" % (qt_id, name, version)
    (value, found) = fileCache.get(key)
    if (not found) or version == 1000000000:
        ret = run_sql("SELECT data FROM qtattach WHERE qtemplate = %s AND name = %s AND version = "
                      "  (SELECT MAX(version) FROM qtattach WHERE "
                      " qtemplate=%s AND version <= %s AND name=%s);", (qt_id, name, qt_id, version, name))
        if ret:
            data = str(ret[0][0])
            fileCache.set(key, data)
            return data
        fileCache.set(key, False)
        return False
    return value


def getExamQTemplatesInPosition(exam_id, position):
    """ Return the question templates in the given position in the exam, or 0."""
    assert isinstance(exam_id, int)
    assert isinstance(position, int)
    ret = run_sql("SELECT qtemplate FROM examqtemplates WHERE exam=%s AND position=%s;", (exam_id, position))
    if ret:
        qtemplates = [int(row[0]) for row in ret]
        return qtemplates
    return []


def getQTemplatePositionInExam(exam_id, qt_id):
    """Return the position a given question template holds in the exam"""
    assert isinstance(exam_id, int)
    assert isinstance(qt_id, int)
    ret = run_sql("SELECT position FROM examqtemplates WHERE exam=%s AND qtemplate=%s;", (exam_id, qt_id))
    if ret:
        return int(ret[0][0])
    return None


def getQTemplatePositionInTopic(qt_id, topic_id):
    """ Fetch the position of a question template in a topic. """
    assert isinstance(topic_id, int)
    assert isinstance(qt_id, int)
    key = "topic-%d-qtemplate-%d-position" % (topic_id, qt_id)
    obj = MC.get(key)
    if not obj is None:
        return int(obj)
    ret = run_sql("SELECT position FROM questiontopics WHERE qtemplate=%s AND topic=%s;", (qt_id, topic_id))
    if ret:
        MC.set(key, ret[0][0], 120)  # remember for 2 minutes
        return int(ret[0][0])
    return False


def getMaxQTemplatePositionInTopic(topic_id):
    """ Fetch the maximum position of a question template in a topic."""
    assert isinstance(topic_id, int)
    res = run_sql("""SELECT MAX(position) FROM questiontopics WHERE topic=%s; """, (topic_id,))
    if not res:
        return 0
    return res[0][0]


def getQTVariations(qt_id, version=1000000000):
    """ Return all variations of a question template."""
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    if version == 1000000000:
        version = getQTVersion(qt_id)
    ret = {}
    res = run_sql("SELECT variation, data FROM qtvariations WHERE qtemplate=%s AND version ="
                  " (SELECT MAX(version) FROM qtvariations WHERE "
                  "   qtemplate=%s AND version <= %s)", (qt_id, qt_id, version))
    if not res:
        log(WARN, "No Variation found for qtid=%d, version=%d" % (qt_id, version))
        return []
    for row in res:
        result = str(row[1])
        ret[row[0]] = cPickle.loads(result)
    return ret


def getQTVariation(qt_id, variation, version=1000000000):
    """ Return a specific variation of a question template."""
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    assert isinstance(variation, int)
    if version == 1000000000:
        version = getQTVersion(qt_id)
    res = run_sql("SELECT data FROM qtvariations WHERE qtemplate=%s AND variation=%s AND version = "
                  "(SELECT MAX(version) FROM qtvariations WHERE "
                  "qtemplate=%s AND version <= %s)", (qt_id, variation, qt_id, version))
    if not res:
        log(WARN, "Request for unknown question template variation. (%d, %d, %d)" % (qt_id, variation, version))
        return None
    result = None
    data = None
    try:
        result = str(res[0][0])
        data = cPickle.loads(result)
    except TypeError:
        log(WARN, "Type error trying to cpickle.loads(%s) for (%s, %s, %s)" % (type(result), qt_id, variation, version))
    return data


def getQTNumVariations(qt_id, version=1000000000):
    """ Return the number of variations for a question template. """
    assert isinstance(qt_id, int)
    assert isinstance(version, int)
    if version == 1000000000:
        version = getQTVersion(qt_id)
    ret = run_sql("""SELECT MAX(variation) FROM qtvariations
                        WHERE qtemplate=%s AND version = (
                         SELECT MAX(version) FROM qtvariations
                             WHERE qtemplate=%s AND version <= %s)""",
                  (qt_id, qt_id, int(version)))
    try:
        num = int(ret[0][0])
    except BaseException, err:
        log(WARN, "No Variation found for qtid=%d, version=%d: %s" % (qt_id, version, err))
        return 0
    return num


def createQAttachment(qt_id, variation, name, mimetype, data, version):
    """ Create a new Question Attachment using given data."""
    assert isinstance(qt_id, int)
    assert isinstance(variation, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    assert isinstance(mimetype, str) or isinstance(mimetype, unicode)
    assert isinstance(data, str) or isinstance(data, unicode)
    assert isinstance(version, int)
    safedata = psycopg2.Binary(data)
    run_sql("""INSERT INTO qattach (qtemplate, variation, mimetype, name, data, version)
                     VALUES (%s, %s, %s, %s, %s, %s);""", (qt_id, variation, mimetype, name, safedata, version))


def createQTAttachment(qt_id, name, mimetype, data, version):
    """ Create a new Question Template Attachment using given data."""
    assert isinstance(qt_id, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    assert isinstance(mimetype, str) or isinstance(mimetype, unicode)
    assert isinstance(data, str) or isinstance(data, unicode)
    assert isinstance(version, int)
    key = "qtemplateattach/%d/%s/%d" % (qt_id, name, version)
    MC.delete(key)
    if not data:
        data = ""
    if isinstance(data, unicode):
        data = data.encode("utf8")
    safedata = psycopg2.Binary(data)
    run_sql("""INSERT INTO qtattach (qtemplate, mimetype, name, data, version)
                     VALUES (%s, %s, %s, %s, %s);""", (qt_id, mimetype, name, safedata, version))
    return None


def createQuestion(qt_id, name, student, status, variation, version, exam):
    """ Add a question (instance) to the database."""
    assert isinstance(qt_id, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    assert isinstance(student, int)
    assert isinstance(status, int)
    assert isinstance(variation, int)
    assert isinstance(version, int)
    assert isinstance(exam, int)
    conn = dbpool.begin()
    conn.run_sql("""INSERT INTO questions (qtemplate, name, student, status, variation, version, exam)
               VALUES (%s, %s, %s, %s, %s, %s, %s);""", (qt_id, name, student, status, variation, version, exam ))
    res = conn.run_sql("SELECT currval('questions_question_seq')")
    dbpool.commit(conn)
    if not res:
        log(ERROR, "CreateQuestion(%d, %s, %d, %s, %d, %d, %d) may have failed." % (
                qt_id, name, student, status, variation, version, exam))
        return None
    return res[0][0]


def updateQTemplateTitle(qt_id, title):
    """ Update the title of a question template. """
    assert isinstance(qt_id, int)
    assert isinstance(title, str) or isinstance(title, unicode)
    key = "qtemplate-%d-name" % qt_id
    MC.delete(key)
    sql = "UPDATE qtemplates SET title = %s WHERE qtemplate = %s;"
    params = (title, qt_id)
    run_sql(sql, params)


def updateQTemplateOwner(qt_id, owner):
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


def updateQTemplateMaxScore(qt_id, scoremax):
    """ Update the maximum score of a question template. """
    assert isinstance(qt_id, int)
    assert isinstance(scoremax, float) or scoremax is None
    key = "qtemplate-%d-maxscore" % qt_id
    MC.delete(key)
    sql = """UPDATE qtemplates SET scoremax=%s WHERE qtemplate=%s;"""
    params = (scoremax, qt_id)
    run_sql(sql, params)


def updateQTemplateMarker(qt_id, marker):
    """ Update the marker of a question template."""
    assert isinstance(qt_id, int)
    assert isinstance(marker, int)
    sql = """UPDATE qtemplates SET marker=%s WHERE qtemplate=%s;"""
    params = (marker, qt_id)
    run_sql(sql, params)


def updateExamQTemplatesInPosition(exam_id, position, qtlist):
    """ Set the qtemplates at a given position in the exam to match
        the passed list. If we get qtlist = [0], we remove that position.
    """
    assert isinstance(exam_id, int)
    assert isinstance(position, int)
    assert isinstance(qtlist, list)
    # First remove the current set
    run_sql("DELETE FROM examqtemplates WHERE exam=%s AND position=%s;", (exam_id, position))
    # Now insert the new set
    for alt in qtlist:
        if alt > 0:
            run_sql("INSERT INTO examqtemplates (exam, position, qtemplate) VALUES (%s,%s,%s);",
                    (exam_id, position, alt))


def updateQTemplatePosition(qt_id, topic_id, position):
    """ Update the position a question template holds in a topic."""
    assert isinstance(qt_id, int)
    assert isinstance(position, int)
    assert isinstance(topic_id, int)
    previous = getQTemplatePositionInTopic(qt_id, topic_id)
    key = "topic-%d-qtemplate-%d-position" % (topic_id, qt_id)
    MC.delete(key)
    key = "topic-%d-numquestions" % topic_id
    MC.delete(key)
    key = "topic-%d-qtemplates" % topic_id
    MC.delete(key)
    sql = """UPDATE questiontopics SET position=%s WHERE topic=%s AND qtemplate=%s;"""
    params = (position, topic_id, qt_id)
    if not previous is False:
        run_sql(sql, params)
    else:
        addQTemplateToTopic(qt_id, topic_id, position)


def moveQTemplateToTopic(qt_id, topic_id):
    """ Move a question template to a different sub category."""
    assert isinstance(qt_id, int)
    assert isinstance(topic_id, int)
    key = "topic-%d-numquestions" % topic_id
    MC.delete(key)
    key = "topic-%d-qtemplates" % topic_id
    MC.delete(key)
    key = "topic-%d-qtemplate-%d-position" % (topic_id, qt_id)
    MC.delete(key)

    sql = "SELECT topic FROM questiontopics WHERE qtemplate=%s"
    params = (qt_id,)
    ret = run_sql(sql, params)
    if ret:
        for row in ret:
            fromtopic = int(row[0])
            key = "topic-%d-numquestions" % fromtopic
            MC.delete(key)
            key = "topic-%d-qtemplates" % fromtopic
            MC.delete(key)
            key = "topic-%d-qtemplate-%d-position" % (fromtopic, qt_id)
            MC.delete(key)
    run_sql("""UPDATE questiontopics SET topic=%s WHERE qtemplate=%s;""", (topic_id, qt_id))


def addQTemplateToTopic(qt_id, topic_id, position=0):
    """ Put the question template into the topic."""
    assert isinstance(qt_id, int)
    assert isinstance(topic_id, int)
    assert isinstance(position, int)
    run_sql("INSERT INTO questiontopics (qtemplate, topic, position) VALUES (%s, %s, %s)", (qt_id, topic_id, position))
    key = "topic-%d-numquestions" % topic_id
    MC.delete(key)
    key = "topic-%d-qtemplates" % topic_id
    MC.delete(key)


def copyQTemplateAll(qt_id):
    """ Make an identical copy of a question template,
        including all attachments.
    """
    assert isinstance(qt_id, int)
    newid = copyQTemplate(qt_id)
    if newid <= 0:
        return 0
    attachments = getQTAttachments(qt_id)
    newversion = getQTVersion(newid)
    for name in attachments:
        createQTAttachment(newid, name, getQTAttachmentMimeType(qt_id, name), getQTAttachment(qt_id, name), newversion)
    try:
        variations = getQTVariations(qt_id)
        for variation in variations.keys():
            addQTVariation(newid, variation, variations[variation], newversion)
    except AttributeError, err:
        log(WARN, "Copying a qtemplate %s with no variations. '%s'" % (qt_id, err))
    return newid


def copyQTAttachment(sourceqtid, destqtid, name):
    """ Copy an attachment from one template to another.
    """
    assert isinstance(sourceqtid, int)
    assert isinstance(destqtid, int)
    assert isinstance(name, str) or isinstance(name, unicode)
    createQTAttachment(destqtid, name, getQTAttachmentMimeType(sourceqtid, name),
                       getQTAttachment(sourceqtid, name), getQTVersion(destqtid))


def copyQTemplate(qt_id):
    """ Make an identical copy of a question template entry.
        Returns the new qtemplate id.
    """
    assert isinstance(qt_id, int)
    res = run_sql("SELECT owner, title, description, marker, scoremax, status FROM qtemplates WHERE qtemplate = %s",
                  qt_id)
    if not res:
        raise KeyError("QTemplate %d not found" % qt_id)
    orig = res[0]
    newid = createQTemplate(int(orig[0]), orig[1], orig[2], orig[3], orig[4], int(orig[5]))
    if newid <= 0:
        raise IOError("Unable to create copy of QTemplate %d" % qt_id)
    return newid


def addQTVariation(qt_id, variation, data, version):
    """ Add a variation to the question template. """
    assert isinstance(qt_id, int)
    assert isinstance(variation, int)
#    assert isinstance(data, str) or isinstance(data, unicode)
    assert isinstance(version, int)
    pick = cPickle.dumps(data)
    safedata = psycopg2.Binary(pick)
    run_sql("INSERT INTO qtvariations (qtemplate, variation, data, version) VALUES (%s, %s, %s, %s)",
            (qt_id, variation, safedata, version))


def createQTemplate(owner, title, desc, marker, scoremax, status):
    """ Create a new Question Template. """
    assert isinstance(owner, int)
    assert isinstance(title, str) or isinstance(title, unicode)
    assert isinstance(desc, str) or isinstance(desc, unicode)
    assert isinstance(marker, int)
    assert isinstance(scoremax, float)
    assert isinstance(status, int)
    conn = dbpool.begin()
    conn.run_sql("INSERT INTO qtemplates (owner, title, description, marker, scoremax, status, version) "
                 "VALUES (%s, %s, %s, %s, %s, %s, 2);",
                 (owner, title, desc, marker, scoremax, status))
    res = conn.run_sql("SELECT currval('qtemplates_qtemplate_seq')")
    dbpool.commit(conn)
    if res:
        return int(res[0][0])
    log(ERROR, "createQT may have failed(%d, %s, %s, %d, %s, %s)" % (owner, title, desc, marker, scoremax, status))


def _serialize_courseexaminfo(info):
    """ Serialize the structure for, eg. cache.
        The dates, especially, need work before JSON
    """
    FMT = '%Y-%m-%d %H:%M:%S'
    safe = {}
    for k, exam in info.iteritems():
        safe[k] = exam
        safe[k]['start'] = exam['start'].strftime(FMT)
        safe[k]['end'] = exam['end'].strftime(FMT)
    return json.dumps(safe)


def _deserialize_courseexaminfo(obj):
    """ Deserialize a serialized exam info structure."""
    FMT = '%Y-%m-%d %H:%M:%S'
    safe = json.loads(obj)
    info = {}
    for k, exam in safe.iteritems():
        info[k] = exam
        info[k]['start'] = datetime.datetime.strptime(exam['start'], FMT)
        info[k]['end'] = datetime.datetime.strptime(exam['end'], FMT)
    return info


def getCourseExamInfoAll(course_id, previous_years=False):
    """ Return a summary of information about all current exams in the course
        {id, course, name, description, start, duration, end, type}
    """
    assert isinstance(course_id, int)
    assert isinstance(previous_years, bool)
    if previous_years:
        key = "course-exam-all-%s-prevyears" % course_id
    else:
        key = "course-exam-all-%s" % course_id
    obj = MC.get(key)
    if obj:
        return _deserialize_courseexaminfo(obj)

    if previous_years:
        sql = """SELECT exam, course, title, "type", "start", "end", description,
                            duration, to_char("start", 'DD Mon'), to_char("start", 'hh:mm'),
                            to_char("end", 'DD Mon'), to_char("end", 'hh:mm')
                     FROM exams WHERE course='%s' AND archived='0' ORDER BY "start";"""
    else:
        sql = """SELECT exam, course, title, "type", "start", "end", description,
                            duration, to_char("start", 'DD Mon'), to_char("start", 'hh:mm'),
                            to_char("end", 'DD Mon'), to_char("end", 'hh:mm')
                     FROM exams WHERE course='%s' AND archived='0' AND extract('year' from "end") = extract('year' from now()) ORDER BY "start";"""
    params = (course_id,)
    ret = run_sql(sql, params)
    info = {}
    if ret:
        for row in ret:
            info[int(row[0])] = {'id': row[0], 'course': row[1], 'name': row[2], 'type': row[3],
                                 'start': row[4], 'end': row[5], 'description': row[6], 'duration': row[7],
                                 'startdate': row[8], 'starttime': row[9], 'enddate': row[10], 'endtime': row[11]}
    MC.set(key, _serialize_courseexaminfo(info),
           60) # 60 second cache. enough to take the edge off an exam start peak load
    return info


def addExamQuestion(user, exam, question, position):
    """Record that the student was assigned the given question for their assessment. """
    assert isinstance(user, int)
    assert isinstance(exam, int)
    assert isinstance(question, int)
    assert isinstance(position, int)
    sql = """SELECT id FROM examquestions
            WHERE exam = %s AND student = %s AND position = %s AND question = %s;"""
    params = (exam, user, position, question)
    ret = run_sql(sql, params)
    if ret:  # already exists
        return
    run_sql("INSERT INTO examquestions (exam, student, position, question)  VALUES (%s, %s, %s, %s);",
            (exam, user, position, question))
    touchUserExam(exam, user)

#
# def getExamQuestions(user, exam):
#     """Return an ordered list of questions used in the exam for the student.
#     """
#
#     ret = getFields(
#         table="examquestions",
#         fields=("position", "question"),
#         where="exam='%d' and student='%d'" % (int(exam), int(user)))
#     if ret:
#         questions = [int(row['question']) for row in ret]
#         return questions
#     return []

def getStudentQuestionPracticeNum(user_id, qt_id):
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


def convertSecondsToHuman(seconds):
    """Convert a number of seconds to a human readable string, eg  "8 days"
    """
    assert isinstance(seconds, int) or isinstance(seconds, float)
    perday = 86400
    return "%d days ago" % int(seconds / perday)


def getIndividualPracticeStats(user_id, qt_id):
    """ Return Data on the scores of individual practices. it is used for displaying Individual Practise Data section
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


def getStudentQuestionPracticeStats(user_id, qt_id, num=3):
    """Return data on the scores obtained while practicing the given question the last 'num' times.
       Exclude assessed scores.  If num is not provided, defaults to 3. If num is 0, give stats for all.
       Returns list of last 'num' practices:
       {'score': score, 'question':question id, 'age': seconds since practiced }
       New Changes: set up a time period. It only shows the stats within 30 secs to 2 hrs.
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
            ageseconds = 10000000000 # if we can't tell we assume it's from before we tracked it
            age = row[2]
            try:
                age = int(age)
                ageseconds = age
                if age > 63000000:    # more than two years
                    age = "more than 2 years"
                else:
                    age = convertSecondsToHuman(age)
            except (TypeError, ValueError):
                age = "more than 2 years"
            stats.append({'score': float(row[0]), 'question': int(row[1]), 'age': age, 'ageseconds': ageseconds})

        return stats[::-1]   # reverse it so they're in time order
    return None


def fetchQuestionStatsInClass(course, qt_id):
    """Fetch a bunch of statistics about the given question for the class
    """
    assert isinstance(course, int)
    assert isinstance(qt_id, int)
    sql = """SELECT
                 COUNT(question), AVG(score), STDDEV(score), MAX(score), MIN(score)
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


def setMessage(name, message):
    """Store a message
    """
    assert isinstance(name, str) or isinstance(name, unicode)
    assert isinstance(message, str) or isinstance(message, unicode)

    ret = run_sql("SELECT COUNT(message) FROM messages WHERE name=%s;", (name,))
    if ret and len(ret) and int(ret[0][0]) >= 1:
        run_sql("UPDATE messages SET message=%s WHERE name=%s;", (message, name))
        log(INFO, "Message %s updated to %s." % (name, message))
    else:
        run_sql("INSERT INTO messages (name, message) VALUES (%s, %s);", (name, message))
        log(INFO, "Message %s inserted as %s." % (name, message))


def getMessage(name):
    """Retrieve a message
    """
    assert isinstance(name, str) or isinstance(name, unicode)

    ret = run_sql("SELECT message FROM messages WHERE name=%s;", (name,))
    if not ret:
        return ""
    return ret[0][0]


def touchUserExam(exam, user):
    """ Update the lastchange field on a user exam so other places can tell that
        something changed. This should probably be done any time one of the
        following changes:
            userexam fields on that row
            question/guess in the exam changes
    """
    assert isinstance(exam, int)
    assert isinstance(user, int)
    sql = "UPDATE userexams SET lastchange = NOW() WHERE exam=%s AND student=%s;"
    params = (exam, user)
    run_sql(sql, params)


def getQTemplateEditor(qt_id):
    """ Return which type of editor the question should use.
        OQE | Raw
    """
    assert isinstance(qt_id, int)
    etype = "Raw"
    atts = getQTAttachments(qt_id)
    for att in atts:
        if att.endswith(".oqe"):
            etype = "OQE"
    return etype


def getDBVersion():
    """ Return an string representing the database version
        If it's too old to have a configuration field, then use some heuristics.
    """

    # We have a setting, easy
    try:
        ret = run_sql("SELECT dbversion FROM config;")
        if ret:
            return ret[0][0]
    except psycopg2.DatabaseError:
        pass


    # We don't have a setting, need to figure it out
    try: # stats_prac_q_course was added for 3.9.1
        ret = run_sql("SELECT 1 FROM stats_prac_q_course;")
        if ret:
            return "3.9.1"

    except psycopg2.DatabaseError:
        return "3.6"

    return "unknown"


def upgradeDB():
    """ See if the database needs upgrading and, if so, do it
    """

    dbver = getDBVersion()