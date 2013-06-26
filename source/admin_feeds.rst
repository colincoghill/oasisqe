..

External Systems
================

To obtain information from other systems OASIS uses "feeds". These are
small scripts which, when run, will communicate with other systems. For
example, one might connect to a central LDAP server and retrieve enrolment
information.

.. sidebar:: License Aside

   One of the reasons for implementing external links as small scripts with
   a defined interface is that they are not bound by the AGPL license
   that OASIS comes under, and do not have to be written in Python. You
   are free to modify any of the samples that come with OASIS or write your
   own, in other languages, without having to provide their source code to
   other parties.


.. image:: admin_feeds_example.png
   :width: 400px

You can have different feeds connecting to different systems if you wish.
There are currently two supported types of feed:

Group Feed
^^^^^^^^^^

Group Feed scripts tell OASIS how users are arranged into groups. For example: students
enrolled in courses, or groups of tutors.

When run, the feed scripts should output a one line status code followed by a simple list of usernames, one per line.

.. code::

   OK
   ccog001
   fsmi324
   jblo034


User Account Feed
^^^^^^^^^^^^^^^^^

User account feeds tell OASIS how to look up details on users it has not seen before. For example
when "fjon032" logs in for the first time, OASIS will run the User Account Feed scripts and expect
one of them to return the user's full name and email address.

.. code::

   uname: fjon032
   fullname: Freddie Jones
   email: f.jones@example.com


No Feeds
^^^^^^^^

It is entirely possible to run OASIS as a standalone system, without configuring any feeds. It
will look after its own user accounts and groups. However, feeds allow you to integrate OASIS
with other systems which may already look after accounts and groups for you.


