# Test that practice UI is working

from unittest import TestCase
import re

from logging import getLogger
from oasis import app
from oasis.lib import DB, Courses

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


class TestPractice(TestCase):

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

    def test_practice_top(self):
        """ Does top practice page load?
        :return:
        """

        with self.app.test_client() as c:

            s = self.login(ADMIN_UNAME, self.adminpass, client=c)
            self.assertNotIn("CSRF token missing or incorrect", s.data)
            self.assertEqual(s.status, "200 OK")
            self.assertIn("<div id='whoami'>Admin </div>", s.data)

            s = c.get('/practice/top', follow_redirects=True)
            self.assertEqual(s.status, "200 OK")
            self.assertIn("Choose A Course", s.data)

    def test_practice_course_list(self):
        """ Check the list of courses is reasonably ok
        :return:
        """
        with self.app.test_client() as c:

            self.login(ADMIN_UNAME, self.adminpass, client=c)

            s = c.get('/practice/top', follow_redirects=True)
            self.assertEqual(s.status, "200 OK")
            self.assertIn("Choose A Course", s.data)

            self.assertNotIn("TESTCOURSE1", s.data)

            # create a course, set it visible, is it there?
            course_id = Courses.create("TESTCOURSE1", "unit tests", 1, 1)
            Courses.create_config(course_id, "casual", 1)
            Courses.set_active(course_id, True)
            Courses.set_prac_vis(course_id, "all")

            s = c.get('/practice/top', follow_redirects=True)
            self.assertEqual(s.status, "200 OK")
            self.assertIn("Choose A Course", s.data)

            self.assertIn("TESTCOURSE1", s.data)
            self.assertNotIn("TESTCOURSE2", s.data)

            # create a second course, set it visible, is it there?
            course_id = Courses.create("TESTCOURSE2", "unit tests", 1, 1)
            Courses.create_config(course_id, "casual", 1)
            Courses.set_active(course_id, True)
            Courses.set_prac_vis(course_id, "all")

            s = c.get('/practice/top', follow_redirects=True)
            self.assertEqual(s.status, "200 OK")
            self.assertIn("Choose A Course", s.data)

            self.assertIn("TESTCOURSE1", s.data)
            self.assertIn("TESTCOURSE2", s.data)

            # create a third course, set it not visible
            course_id = Courses.create("TESTCOURSE3", "unit tests", 1, 1)
            Courses.create_config(course_id, "casual", 1)
            Courses.set_active(course_id, True)
            Courses.set_prac_vis(course_id, "none")

            s = c.get('/practice/top', follow_redirects=True)
            self.assertEqual(s.status, "200 OK")
            self.assertIn("Choose A Course", s.data)

            self.assertIn("TESTCOURSE1", s.data)
            self.assertIn("TESTCOURSE2", s.data)
            # admin can still see it
            self.assertIn("TESTCOURSE3", s.data)

    def test_practice_topic_list(self):

        with self.app.test_client() as c:

            self.login(ADMIN_UNAME, self.adminpass, client=c)

            s = c.get('/practice/top', follow_redirects=True)
            self.assertEqual(s.status, "200 OK")
            self.assertIn("Choose A Course", s.data)

            self.assertNotIn("TESTCOURSE10", s.data)

            course_id = Courses.create("TESTCOURSE10", "unit tests", 1, 1)
            Courses.create_config(course_id, "casual", 1)
            Courses.set_active(course_id, True)
            Courses.set_prac_vis(course_id, "all")

            s = c.get('/practice/top', follow_redirects=True)
            self.assertEqual(s.status, "200 OK")
            self.assertIn("Choose A Course", s.data)

            self.assertIn("TESTCOURSE10", s.data)

            s = c.get('/practice/coursequestions/%s' % course_id)

            self.assertIn("<h2>TESTCOURSE10 (unit tests)</h2>", s.data)
            self.assertIn("Select a Topic", s.data)
