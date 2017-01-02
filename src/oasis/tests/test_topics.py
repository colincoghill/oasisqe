# Test that topic functionality is working

from unittest import TestCase

from oasis.lib import DB, Topics, Courses, Practice


class TestTopics(TestCase):
    @classmethod
    def setUpClass(cls):
        DB.MC.flush_all()

    def test_create_topic(self):
        """ Fetch a topic back and check it
        """

        course_id = Courses.create("TEST101", "Test topic position logic", 1, 1)

        self.assertDictContainsSubset(
            {course_id:
                 {'active': 1,
                  'assess_visibility': 'enrol',
                  'id': course_id,
                  'name': 'TEST101',
                  'owner': 1,
                  'practice_visibility': 'all',
                  'title': 'Test topic position logic',
                  'type': 1
                  }
             },
            Courses.get_courses_dict(),
        )

        topic1_id = Topics.create(course_id, "TESTTOPIC1", 1, 2)
        topic2_id = Topics.create(course_id, "TESTTOPIC2", 3, 3)

        self.assertGreater(topic1_id, 0)
        self.assertIsInstance(topic1_id, int)

        self.assertGreater(topic2_id, 0)
        self.assertIsInstance(topic2_id, int)

        self.assertNotEqual(topic1_id, topic2_id)

        topic1 = Topics.get_topic(topic1_id)
        topic2 = Topics.get_topic(topic2_id)

        self.assertEqual(topic1['id'], topic1_id)
        self.assertEqual(topic2['id'], topic2_id)
        self.assertEqual(topic1['title'], "TESTTOPIC1")
        self.assertEqual(topic2['title'], "TESTTOPIC2")
        self.assertEqual(topic1['visibility'], 1)
        self.assertEqual(topic2['visibility'], 3)

        self.assertEqual(Topics.get_name(topic1_id), topic1['title'])

        Topics.set_name(topic1_id, "NEWNAME1")
        self.assertEqual(Topics.get_name(topic1_id), "NEWNAME1")

        self.assertEqual(Topics.get_num_qs(topic1_id), 0)

        self.assertEqual(Topics.get_pos(topic1_id), 2)

        Topics.set_pos(topic1_id, 8)
        self.assertEqual(Topics.get_pos(topic1_id), 8)

    def test_create_qtemplate(self):
        """ Test qtemplates creation
        """

        qt1_id = DB.create_qt(1, "TESTQ1", "Test question 1", 0, 5.0, 1)
        qt2_id = DB.create_qt(1, "TESTQ2", "Test question 2", 0, 4.1, 2)

        self.assertIsInstance(qt1_id, int)
        self.assertIsInstance(qt2_id, int)

        qt1 = DB.get_qtemplate(qt1_id)
        qt2 = DB.get_qtemplate(qt2_id)

        self.assertEqual(qt1['title'], "TESTQ1")
        self.assertEqual(qt2['title'], "TESTQ2")
        self.assertEqual(qt1['description'], "Test question 1")
        self.assertEqual(qt2['description'], "Test question 2")

        course_id = Courses.create("TEST107", "Test create qtemplate", 1, 1)
        topic1_id = Topics.create(course_id, "TESTTOPIC9", 1, 2)

        qt3_id = DB.create_qt(1, "TESTQ3", "Test question 3", 0, 5.0, 1, topic1_id)

        self.assertIsInstance(qt3_id, int)

        qt3 = DB.get_qtemplate(qt3_id)
        self.assertEqual(qt3['title'], "TESTQ3")
        self.assertEqual(qt3['description'], "Test question 3")
        self.assertEqual(DB.get_topic_for_qtemplate(qt3_id), topic1_id)

    def test_topic_position(self):
        """ Test putting qtemplates into topics and moving them around
        """

        course_id = Courses.create("TEST101", "Test topic position logic", 1, 1)
        topic1_id = Topics.create(course_id, "TESTTOPIC1", 1, 2)
        topic2_id = Topics.create(course_id, "TESTTOPIC2", 3, 3)
        qt1_id = DB.create_qt(1, "TESTQ1", "Test question 1", 0, 5.0, 1)
        qt2_id = DB.create_qt(1, "TESTQ2", "Test question 2", 0, 4.1, 2, topic1_id)

        DB.move_qt_to_topic(qt1_id, topic1_id)

        self.assertEqual(DB.get_qtemplate_practice_pos(qt1_id), 0)
        self.assertEqual(DB.get_qtemplate_practice_pos(qt2_id), 0)

        self.assertEqual(DB.get_topic_for_qtemplate(qt1_id), topic1_id)
        self.assertEqual(DB.get_topic_for_qtemplate(qt2_id), topic1_id)

        DB.update_qt_practice_pos(qt1_id, 3)
        DB.update_qt_practice_pos(qt2_id, 2)

        self.assertEqual(DB.get_qtemplate_practice_pos(qt1_id), 3)
        self.assertEqual(DB.get_qtemplate_practice_pos(qt2_id), 2)

        self.assertEqual(DB.get_qtemplate_practice_pos(qt1_id), 3, "Broken cache?")
        self.assertEqual(DB.get_qtemplate_practice_pos(qt2_id), 2, "Broken cache?")

        DB.update_qt_practice_pos(qt1_id, 0)
        DB.update_qt_practice_pos(qt2_id, -1)

        self.assertEqual(DB.get_qtemplate_practice_pos(qt1_id), 0)
        self.assertEqual(DB.get_qtemplate_practice_pos(qt2_id), -1)

        self.assertEqual(DB.get_qtemplate_practice_pos(qt1_id), 0, "Broken cache?")
        self.assertEqual(DB.get_qtemplate_practice_pos(qt2_id), -1, "Broken cache?")

        qts = Topics.get_qts(topic1_id)

        self.assertIn(qt1_id, qts)
        self.assertIn(qt2_id, qts)
        self.assertEqual(len(qts), 2)

        DB.move_qt_to_topic(qt1_id, topic2_id)
        qts = Topics.get_qts(topic1_id)

        self.assertNotIn(qt1_id, qts)
        self.assertIn(qt2_id, qts)
        self.assertEqual(len(qts), 1)

    def test_topic_nextprev(self):
        """ Do the "next/previous" options in practice work?
        """

        course_id = Courses.create("TEST101", "Test topic next/prev logic", 1, 1)
        topic1_id = Topics.create(course_id, "TESTTOPIC1", 1, 2)

        qt1_id = DB.create_qt(1, "TESTQ1", "Test question 1", 0, 5.0, 1)
        qt2_id = DB.create_qt(1, "TESTQ2", "Test question 2", 0, 4.1, 2)
        qt3_id = DB.create_qt(1, "TESTQ3", "Test question 3", 0, 0.0, 2)
        qt4_id = DB.create_qt(1, "TESTQ4", "Test question 4", 0, 2.0, 2)

        DB.move_qt_to_topic(qt1_id, topic1_id)
        DB.move_qt_to_topic(qt2_id, topic1_id)
        DB.move_qt_to_topic(qt3_id, topic1_id)
        DB.move_qt_to_topic(qt4_id, topic1_id)

        DB.update_qt_practice_pos(qt1_id, 1)
        DB.update_qt_practice_pos(qt2_id, 2)
        DB.update_qt_practice_pos(qt3_id, 3)
        DB.update_qt_practice_pos(qt4_id, 4)

        qts = Topics.get_qts(topic1_id)
        self.assertIn(qt1_id, qts)
        self.assertIn(qt2_id, qts)
        self.assertIn(qt3_id, qts)
        self.assertIn(qt4_id, qts)
        self.assertEqual(len(qts), 4)

        self.assertTupleEqual(Practice.get_next_prev_pos(qt1_id, topic1_id), (None, 2))
        self.assertTupleEqual(Practice.get_next_prev_pos(qt2_id, topic1_id), (1, 3))
        self.assertTupleEqual(Practice.get_next_prev_pos(qt3_id, topic1_id), (2, 4))
        self.assertTupleEqual(Practice.get_next_prev_pos(qt4_id, topic1_id), (3, None))

        DB.update_qt_practice_pos(qt2_id, 3)

        self.assertEqual(DB.get_qtemplate_practice_pos(qt1_id), 1)
        self.assertEqual(DB.get_qtemplate_practice_pos(qt2_id), 3)
        self.assertEqual(DB.get_qtemplate_practice_pos(qt3_id), 3)
        self.assertEqual(DB.get_qtemplate_practice_pos(qt4_id), 4)

        self.assertTupleEqual(Practice.get_next_prev_pos(qt1_id, topic1_id), (None, 3))
        self.assertTupleEqual(Practice.get_next_prev_pos(qt2_id, topic1_id), (1, 4))
        self.assertTupleEqual(Practice.get_next_prev_pos(qt3_id, topic1_id), (1, 4))
        self.assertTupleEqual(Practice.get_next_prev_pos(qt4_id, topic1_id), (3, None))

        self.assertTupleEqual(Practice.get_next_prev_pos(qt4_id, None), (None, None))

    def test_do_question(self):
        """ Do a question"""

        course_id = Courses.create("TEST102", "Test question logic", 1, 1)
        self.assertGreater(course_id, 0)
        topic1_id = Topics.create(course_id, "TESTQUESTIONS1", 1, 2)
        self.assertGreater(topic1_id, 0)
        qt1_id = DB.create_qt(1, "TESTQ9", "Test question 9", 0, 5.0, 1, topic_id=topic1_id)

        self.assertIsNotNone(qt1_id)
        q_id = DB.get_q_by_qt_student(qt1_id, 1)

        self.assertGreater(q_id, 0)
        DB.update_qt_maxscore(qt1_id, 7.0)
        score = DB.get_qt_maxscore(qt1_id)
        self.assertEqual(score, 7.0)
        DB.set_q_viewtime(q_id)
        self.assertIsNotNone(DB.get_q_viewtime(q_id))
