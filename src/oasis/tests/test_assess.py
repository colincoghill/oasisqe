# Test that assessments work

from unittest import TestCase
import re

from logging import getLogger
from oasis import app
import datetime
from oasis.lib import DB, Courses, Exams

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


class TestAssess(TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = app
        cls.app.testing = True
        cls.app.config["TESTING"] = True
        cls.adminpass = DB.generate_admin_passwd()

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