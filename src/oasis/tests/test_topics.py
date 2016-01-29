# Test that topic functionality is working

from oasis.lib import DB, Topics, Courses

course_id = None

def test_create_course():
    """ Make us a course to put stuff in
    """
    global course_id

    course_id = Courses.create("TEST101", "A Test Course", 1, 1)


def test_create_topic():
    """ Create a topic and fetch it back.
    """

    newid = Topics.create(course_id, "TESTTOPIC1",1,2)
    assert newid > 0
    assert isinstance(newid, int)

    newid2 = Topics.create(course_id, "TESTTOPIC2",3,3)
    assert newid2 > 0
    assert isinstance(newid2, int)

    assert newid != newid2

