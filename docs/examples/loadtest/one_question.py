
""" Create a single course, topic, question. Then repeatedly practice the question.

    Usage:   locust -f one_question.py --host http://localhost:8080
"""

ADMIN_PASS = 'devtest'

from locust import HttpLocust, TaskSet


def login(l):
    l.client.post("/oasis/login/local/submit", {"username": "admin", "password": ADMIN_PASS})


def index(l):
    l.client.get("/oasis")


def top(l):
    l.client.get("/oasis/main/top")


def practice_top(l):
    l.client.get("/oasis/practice/top")


def practice_course(l):
    l.client.get("/oasis/practice/coursequestions/1")


def practice_topic(l):
    l.client.get("/oasis/practice/subcategory/1")


def practice_question(l):
    l.client.get("/oasis/practice/question/14/1")


def practice_answer(l):
    l.client.post("/oasis/practice/markquestion/14/11", {"Q_11_ANS_1": '6'})


def setup_top(l):
    l.client.get("/oasis/setup/top")


def setup_courses(l):
    l.client.get("/oasis/setup/courses")


def setup_courses_admin_top(l):
    l.client.get("/oasis/cadmin/1/top")


def setup_courses_admin_topics(l):
    l.client.get("/oasis/cadmin/1/topics")


def assess_top(l):
    l.client.get("/oasis/assess/top")


def news_top(l):
    l.client.get("/oasis/main/news")


def setup_courses_top(l):
    l.client.get("/oasis/setup/courses")


class UserBehavior(TaskSet):
    tasks = {index: 2,
             top: 2,
             practice_top: 5,
             setup_top: 1,
             assess_top: 1,
             news_top: 1,
             setup_courses_top: 1,
             practice_course: 1,
             practice_topic: 1,
             practice_question: 1,
             practice_answer: 1,
             setup_courses: 1,
             setup_courses_admin_top: 1,
             setup_courses_admin_topics: 1
             }

    def on_start(self):

        login(self)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000
