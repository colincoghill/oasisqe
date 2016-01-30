# Test that topic functionality is working

from unittest import TestCase

from oasis.lib import DB, Topics, Courses



# Get created for following (non destructive) tests to make use of
course_id = None
topic1_id = None
topic2_id = None
qt1_id = None
qt2_id = None


class TestTopics(TestCase):

    @classmethod
    def setUpClass(cls):

        cls.course_id = Courses.create("TEST101", "A Test Course", 1, 1)
        cls.topic1_id = Topics.create(cls.course_id, "TESTTOPIC1", 1, 2)
        cls.topic2_id = Topics.create(cls.course_id, "TESTTOPIC2", 3, 3)
        cls.qt1_id = DB.create_qt(1, "TESTQ1", "Test question 1", 0, 5.0, 1)
        cls.qt2_id = DB.create_qt(1, "TESTQ2", "Test question 2", 0, 4.1, 2)

        DB.MC.flush_all()

    def test_create_topic(self):
        """ Fetch a topic back and check it
        """

        self.assertGreater(self.topic1_id, 0)
        self.assertIsInstance(self.topic1_id, int)

        self.assertGreater(self.topic2_id, 0)
        self.assertIsInstance(self.topic2_id, int)

        self.assertNotEqual(self.topic1_id, self.topic2_id)

        topic1 = Topics.get_topic(self.topic1_id)
        topic2 = Topics.get_topic(self.topic2_id)

        self.assertEqual(topic1['id'], self.topic1_id)
        self.assertEqual(topic2['id'], self.topic2_id)
        self.assertEqual(topic1['title'], "TESTTOPIC1")
        self.assertEqual(topic2['title'], "TESTTOPIC2")
        self.assertEqual(topic1['visibility'], 1)
        self.assertEqual(topic2['visibility'], 3)

    def test_create_qtemplate(self):
        """ Test qtemplates creation
        """

        self.assertIsInstance(self.qt1_id, int)
        self.assertIsInstance(self.qt2_id, int)

        qt1 = DB.get_qtemplate(self.qt1_id)
        qt2 = DB.get_qtemplate(self.qt2_id)

        self.assertEqual(qt1['title'], "TESTQ1")
        self.assertEqual(qt2['title'], "TESTQ2")
        self.assertEqual(qt1['description'], "Test question 1")
        self.assertEqual(qt2['description'], "Test question 2")


    def test_topic_position(self):
        """ Test putting qtemplates into topics and moving them around
        """

        DB.move_qt_to_topic(self.qt1_id, self.topic1_id)
        DB.move_qt_to_topic(self.qt2_id, self.topic1_id)

        self.assertEqual(DB.get_qtemplate_practice_pos(self.qt1_id), 0)
        self.assertEqual(DB.get_qtemplate_practice_pos(self.qt2_id), 0)

        self.assertEqual(DB.get_topic_for_qtemplate(self.qt1_id), self.topic1_id)
        self.assertEqual(DB.get_topic_for_qtemplate(self.qt2_id), self.topic1_id)

        DB.update_qt_practice_pos(self.qt1_id, 3)
        DB.update_qt_practice_pos(self.qt2_id, 2)

        self.assertEqual(DB.get_qtemplate_practice_pos(self.qt1_id), 3)
        self.assertEqual(DB.get_qtemplate_practice_pos(self.qt2_id), 2)

        self.assertEqual(DB.get_qtemplate_practice_pos(self.qt1_id), 3, "Broken cache?")
        self.assertEqual(DB.get_qtemplate_practice_pos(self.qt2_id), 2, "Broken cache?")

        DB.update_qt_practice_pos(self.qt1_id, 0)
        DB.update_qt_practice_pos(self.qt2_id, -1)

        self.assertEqual(DB.get_qtemplate_practice_pos(self.qt1_id), 0)
        self.assertEqual(DB.get_qtemplate_practice_pos(self.qt2_id), -1)

        self.assertEqual(DB.get_qtemplate_practice_pos(self.qt1_id), 0, "Broken cache?")
        self.assertEqual(DB.get_qtemplate_practice_pos(self.qt2_id), -1, "Broken cache?")

        qts = Topics.get_qts(self.topic1_id)

        self.assertIn(self.qt1_id, qts)
        self.assertIn(self.qt2_id, qts)
        self.assertEqual(len(qts), 2)


