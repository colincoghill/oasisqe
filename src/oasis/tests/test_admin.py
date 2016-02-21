# Test that group functionality is working

from unittest import TestCase
import datetime
from oasis.lib import DB, Groups, Periods


class TestGroups(TestCase):

    @classmethod
    def setUpClass(cls):

        DB.MC.flush_all()

    def test_create_group(self):
        """ Fetch a group back and check it
        """

        period1 = Periods.Period(name="Period 01",
                                title="Test 01",
                                start=datetime.datetime.now(),
                                finish=datetime.datetime.now(),
                                code="CODE1"
                                )
        period1.save()

        period2 = Periods.Period(name="Period 01")
        self.assertTrue(period2)
        self.assertEqual(period2.title, "Test 01")

        period3 = Periods.Period(code="CODE1")
        self.assertEqual(period2.title, "Test 01")

        self.assertEqual(period2.id, period3.id)

        period4 = Periods.Period(period2.id)
        self.assertEqual(period2.start, period4.start)

        name = "TESTGROUP1"
        title = "Test Group 01"
        gtype = 1
        source = None
        feed = None
        feed_args = ""

        self.assertFalse(Groups.get_ids_by_name(name))
        group = Groups.Group(g_id=0)
        group.name = name
        group.title = title
        group.gtype = gtype
        group.source = source
        group.period = period2.id
        group.feed = feed
        group.feedargs = feed_args
        group.active = True

        group.save()

        self.assertTrue(Groups.get_ids_by_name(name))


