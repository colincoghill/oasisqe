# -*- coding: utf-8 -*-

# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Provide OASIS access through an API, suitable for other software to hook

    At the moment we're just letting users download CSV files and providing
    some backend for AJAX stuff.
"""

from oasis.lib import General, Courses


def get_q_list(topic_id):
    """
    Return a list of questions, sorted by position.
    """
    # TODO: Duplicated in General.get_q_list ?

    questionlist = General.get_q_list(topic_id, None, False)
    if questionlist:
        # At the moment we use -'ve positions to indicate that a question is
        # hidden but when displaying them we want to maintain the sort order.
        for question in questionlist:
            # Usually questions with position 0 are broken or uninteresting
            # so put them at the bottom.
            if question['position'] == 0:
                question['position'] = -10000
        questionlist.sort(key=lambda k: abs(k["position"]))
    else:
        questionlist = []

    return questionlist


def exam_available_q_list(course_id):
    """ Return a list of questions that can be used to create an assessment
    """
    topics = Courses.get_topics_all(course_id, archived=0, numq=False)
    for num, topic in list(topics.items()):
        topic_id = topics[num]['id']
        topics[num]['questions'] = get_q_list(topic_id)
    return topics
