# Test that practice functionality is working

from unittest import TestCase

from oasis.lib import OaConfig, DB
from oasis import app

ADMIN_UNAME = "admin"
ADMIN_PASS = "oasistest"


class TestPractice(TestCase):

    @classmethod
    def setUpClass(cls):

        app.config.update(  # This doesn't seem to work?
            TESTING=True,
            WTF_CSRF_CHECK_DEFAULT=False,
            WTF_CSRF_ENABLED=False
        )
        cls.app = app.test_client()
        DB.MC.flush_all()

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_login(self):
        r = self.login(ADMIN_UNAME, ADMIN_PASS)
        self.assertIn("CSRF token missing or incorrect", r.data)

    def test_practice_top(self):
        """ Make sure the practice top page loads ok
        """
        s = self.app.get('/practice/top', follow_redirects=True)

        # We hit the login page
        self.assertIn("a local OASIS-only account", s.data)

        # So log in
        s = self.login("admin", "oasistest")
        self.assertIn("CSRF token missing or incorrect", s.data)

        # Aha, we need a CSRF token!

