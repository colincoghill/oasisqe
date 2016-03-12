# Test that group functionality is working

from unittest import TestCase
import datetime
from oasis.lib import DB, Groups, Periods, Courses


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


    def test_course_config(self):
        """ Test course configuration templates
        """
        course1_id = Courses.create("TEMPL01", "Test course templates", 1, 1)
        period = Periods.Period(name="TEMPL01",
                                title="Template 01",
                                start=datetime.datetime.now(),
                                finish=datetime.datetime.now(),
                                code="TMPL1"
                                )
        period.save()

        period2 = Periods.Period(code="TMPL1")
        Courses.create_config(course1_id, "large", period2.id)
        groups = Courses.get_groups(course1_id)

        self.assertEqual(len(groups), 1)

        course2_id = Courses.create("TEMPL02", "Test course standard", 1, 1)
        Courses.create_config(course2_id, "standard", period2.id)
        groups = Courses.get_groups(course2_id)

        self.assertEqual(len(groups), 2)

        course3_id = Courses.create("TEMPL03", "Test course demo", 1, 1)
        Courses.create_config(course3_id, "demo", period2.id)
        groups = Courses.get_groups(course3_id)
        self.assertEqual(len(groups), 3)

        self.assertListEqual(groups.keys(), [4,5,6])

        self.assertEqual(groups[4].members(), [])
        self.assertEqual(groups[5].members(), [])
        self.assertEqual(groups[6].members(), [])

        groups[4].add_member(1)
        self.assertEqual(groups[4].members(), [1])
        self.assertEqual(groups[5].members(), [])
        self.assertEqual(groups[6].members(), [])

        groups[4].add_member(1)
        groups[5].add_member(1)
        self.assertEqual(groups[4].members(), [1])
        self.assertEqual(groups[5].members(), [1])

        groups[4].remove_member(1)
        self.assertEqual(groups[4].members(), [])
        self.assertEqual(groups[5].members(), [1])

        self.assertListEqual(groups[4].member_unames(), [])
        self.assertListEqual(groups[5].member_unames(), ["admin"])

        self.assertEqual(groups[4].size(), 0)
        self.assertEqual(groups[5].size(), 1)

        groups[5].flush_members()
        self.assertEqual(groups[5].members(), [])
