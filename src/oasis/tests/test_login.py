# Test that login functionality is working

from unittest import TestCase
import re

from logging import getLogger
from oasis import app
from oasis.lib import DB

L = getLogger("oasisqe")

ADMIN_UNAME = "admin"


# <input type="hidden" name="csrf_token" value="1454892440##2da01a33658b53a9604d6633e45faa2c8f4eec1d" />
csrf_token_input = re.compile(
    r'name="csrf_token".*value="([0-9a-z#A-Z-\.]*)"'
)


def get_csrf_token(data):

    match = csrf_token_input.search(data)
    if match:
        return match.groups()[0]
    return None


class TestLogin(TestCase):

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

    def login(self, username, password, client=None, target=None):

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

    def test_login_csrf(self):
        """ Does the CSRF on the login page work?
        :return:
        """

        s = self.login_no_csrf(ADMIN_UNAME, self.adminpass)
        self.assertIn("CSRF token missing or incorrect", s.data)
        s = self.login(ADMIN_UNAME, self.adminpass)
        self.assertNotIn("CSRF token missing or incorrect", s.data)

    def test_bypass_login(self):
        """ Can we bypass the login page?
        :return:
        """

        with self.app.test_client() as c:
            s = c.get("askldjfhklawehrgfjkl")
            self.assertEquals(s.status, "404 NOT FOUND")

        with self.app.test_client() as c:
            s = c.get('main/top', follow_redirects=True)
            self.assertNotEquals(s.status, "404 NOT FOUND")
            # Not logged in, back at login page
            self.assertIn("a local OASIS-only account", s.data)

        with self.app.test_client() as c:
            s = self.login(ADMIN_UNAME, self.adminpass, client=c)
            self.assertNotIn("CSRF token missing or incorrect", s.data)
            L.error(s.data)
            s = c.get('main/top', follow_redirects=True)
            self.assertEqual(s.status, "200 OK")
            L.error(repr(s))

            # Main top level page
            self.assertIn("The latest news and information about OASIS", s.data)

    def test_main_top(self):

        with self.app.test_client(use_cookies=True) as c:
            s = self.login(ADMIN_UNAME, self.adminpass, client=c)
            L.error(repr(s))
            s = c.get('/main/top')
            # main top level page
            self.assertNotIn("CSRF token missing or incorrect", s.data)
            self.assertIn("The latest news and information about OASIS", s.data)





