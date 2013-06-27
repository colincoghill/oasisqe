.. OASIS QE documentation master file, created by


"Large" Installation
====================

This section will walk through the installation of a large OASIS setup.

In this case, we are installing OASIS in a medium sized University Faculty
with 4000 students. We have two web servers behind a load balancer, and
a separate database server.

OASIS will connect to an existing LDAP server to retrieve student information
and an existing HTTP system for staff information. Course enrolment is primarily
controlled by the central system, although course coordinators can also add
students and tutors themselves.

The university runs courses in three semesters a year, and there is also
Lab Safety content always available to any student who wishes to access it.



