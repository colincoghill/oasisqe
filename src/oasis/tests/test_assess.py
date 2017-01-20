# Test that assessments work

from unittest import TestCase
import re
import os
import tempfile

from logging import getLogger
from oasis import app
import datetime
from oasis.lib import DB, Courses, Exams, External, Topics

L = getLogger("oasisqe")

ADMIN_UNAME = "admin"


# <input type="hidden" name="csrf_token" value="1454892440##2da01a33658b53a9604d6633e45faa2c8f4eec1d" />
csrf_token_input = re.compile(
    r'name="csrf_token".*value="([0-9a-z#A-Z-._]*)"'
)

def get_csrf_token(data):

    match = csrf_token_input.search(data)
    if match:
        return match.groups()[0]
    return None

def create_exported_questions(fname):
    """ Make some questions and export them."""
    # Not really related to assessment, but can use this to create some questions to import and use multiple times
    course_id = Courses.create("TEST106", "Test Question Export", 1, 1)
    topic1_id = Topics.create(course_id, "TESTEXPORT1", 1, 2)
    qt1_id = DB.create_qt(1, "TESTQ1", "Test question 1", 0, 5.0, 1, topic_id=topic1_id)
    ver = DB.get_qt_version(qt1_id)

    data = "2\n|1\n|2\n"
    qvars = [{'A1': "2"}, {'A1': "3"}]
    for row in range(0, len(qvars)):
        DB.add_qt_variation(qt1_id, row + 1, qvars[row], ver)
    DB.create_qt_att(qt1_id, "datfile.dat", "text/plain", data, ver)
    DB.create_qt_att(qt1_id, "qtemplate.html", "text/html", "What is <VAL A1>? <ANSWER 1>", ver)

    qt2_id = DB.create_qt(1, "TESTQ2", "Test question 2", 0, 5.0, 1, topic_id=topic1_id)
    ver = DB.get_qt_version(qt2_id)
    data = "2\n|6\n|7\n"
    qvars = [{'A1': "6"}, {'A1': "7"}]
    for row in range(0, len(qvars)):
        DB.add_qt_variation(qt2_id, row + 1, qvars[row], ver)
    DB.create_qt_att(qt2_id, "datfile.dat", "text/plain", data, ver)
    DB.create_qt_att(qt2_id, "qtemplate.html", "text/html", "Question 2: What is <VAL A1>? <ANSWER 1>", ver)

    qt3_id = DB.create_qt(1, "TESTQ3", "Test question 3", 0, 5.0, 1, topic_id=topic1_id)
    ver = DB.get_qt_version(qt3_id)
    data = "3\n|9\n|10\n|11\n"
    qvars = [{'A1': "9"}, {'A1': "10"}, {'A1': "11"}]
    for row in range(0, len(qvars)):
        DB.add_qt_variation(qt3_id, row + 1, qvars[row], ver)
    DB.create_qt_att(qt3_id, "datfile.dat", "text/plain", data, ver)
    DB.create_qt_att(qt3_id, "qtemplate.html", "text/html", "Question 3: What is <VAL A1>? <ANSWER 1>", ver)

    data = External.topic_to_zip(topic1_id)
    f = open("%s" % fname, mode='w')
    f.write(data)
    f.close()


class TestAssess(TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = app
        cls.app.testing = True
        cls.app.config["TESTING"] = True
        cls.adminpass = DB.generate_admin_passwd()
        (fptr, cls.test_question_fname) = tempfile.mkstemp()
        os.close(fptr)

    def setUp(self):
        create_exported_questions(self.test_question_fname)

    def login_no_csrf(self, username, password):
        c = self.app.test_client()
        return c.post('/login/local/submit', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def login(self, username, password, client=None):

        if not client:
            client = self.app.test_client()

        s = client.get('/login/local/')
        token = get_csrf_token(s.data)
        self.assertIsNotNone(token)
        return client.post('/login/local/submit', data=dict(
            username=username,
            password=password,
            csrf_token=token
            ), follow_redirects=True
        )

    def test_assess_top(self):
        """ Does top assess page load?
        :return:
        """

        with self.app.test_client() as c:

            s = self.login(ADMIN_UNAME, self.adminpass, client=c)
            self.assertNotIn("CSRF token missing or incorrect", s.data)
            self.assertEqual(s.status, "200 OK")
            self.assertIn("<div id='whoami'>Admin </div>", s.data)

            s = c.get('/assess/top', follow_redirects=True)
            self.assertEqual(s.status, "200 OK")
            self.assertIn("Past Assessments", s.data)

    def test_assess_create(self):
        """ Create an empty assessment"""

        course_id = Courses.create("TESTCOURSE5", "unit tests for assessment", 1, 1)
        Courses.create_config(course_id, "casual", 1)
        Courses.set_active(course_id, True)
        Courses.set_prac_vis(course_id, "none")
        Courses.set_assess_vis(course_id, "none")

        title = "Test Assessment 1"
        atype = 2  # assignment
        duration = 60
        code = "123456"
        instant = 1
        instructions = "These are the instructions"
        astart = datetime.datetime.utcnow()
        aend = astart + datetime.timedelta(hours=2)

        exam_id = Exams.create(course_id, 1, title, atype, duration, astart,
                               aend, instructions, code=code, instant=instant)
        self.assertGreater(exam_id, 0)

        topic1_id = Topics.create(course_id, "TESTASSESS1", 1, 1)
        self.assertGreater(topic1_id, 0)

        data = open(self.test_question_fname).read()
        numread = External.import_qts_from_zip(data, topic1_id)
        self.assertEqual(numread, 3)
