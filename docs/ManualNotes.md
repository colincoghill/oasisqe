

At the moment this is a collection of notes, that I will slowly extend and may one day grow up to
be a manual. Borrow liberally from the 2004 user manual.



Installation
============

    see REQUIREMENTS.md and INSTALL.md

* What are the core configuration options?


Setup
=====


Users
-----

* Describe common configurations, eg. with server auth, or with spreadsheet enrolment feeds.

Permissions
-----------

* How do the course permissions work.
* How to assign them.


Courses
-------

* What is a course, how are OASIS topics arranged.

A course is, essentially, a collection of people, questions, and assessments. The usual structure is to arrange these
by topic to mirror an existing school/university course, but it could be done other ways.

Every course has a single co-ordinator, who is primarily responsible for the overall running of the course in OASIS.
They can do everything themselves, or they can assign permissions to others. Permissions are fairly granular, for
example it's possible to assign an assistant to create and check questions in the course - they will not automatically
gain access to students' assessment marks, or be able to see assessments in advance.


Scheduler
---------

* What gets run, when. What does it do. Implications.


Examples
--------

* Set up with local courses, open enrolment only.

Log in as administrator, and navigate to Setup -> Server Administration -> Courses



You should see a listing of courses in the system (if any), and a button allowing you to "Add Course". Press this.

[SCREENSHOT]

Choose a name and a title for the course. The name should be something short. For universities an appropriate name
might be the course code, eg. "PHYSICS101".  The title is a longer name, eg. "Introduction to Physics".


Next, decide how students will be associated with the course:

[SCREENSHOT]

"Open"

"Course Admin"

"External"





* Set up with server auth, enrolment via spreadsheet.



Questions
=========

* What's possible?

* Features.

* The parts of a question. Basic tutorial.


Assessments
===========

* What's possible



Advice
======


Admin
-----

* Setup and troubleshooting
* Monitoring
* Performance
* Scaling


Teaching
--------


* Question design
* Use in a course
* Assessments


Development
-----------

* Advanced questions
* Improving OASIS itself.