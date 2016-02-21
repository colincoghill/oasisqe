# Test that group functionality is working

from unittest import TestCase

from oasis.lib import DB, Groups


class TestGroups(TestCase):

    @classmethod
    def setUpClass(cls):

        DB.MC.flush_all()

    def test_create_group(self):
        """ Fetch a group back and check it
        """

        name = "TESTGROUP1"
        title = "Test Group 01"
        gtype = 1
        source = None
        feed = None
        feed_args = ""
        period = 1

        self.assertFalse(Groups.get_ids_by_name(name))
        group = Groups.Group(g_id=0)
        group.name = name
        group.title = title
        group.gtype = gtype
        group.source = source
        group.period = period
        group.feed = feed
        group.feedargs = feed_args
        group.active = True

        group.save()

        self.assertTrue(Groups.get_ids_by_name(name))

