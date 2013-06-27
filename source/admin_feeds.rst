..

External Systems
================

To obtain information from other systems OASIS uses "feeds". These are
small scripts which, when run, will communicate with other systems. For
example, one might connect to a central LDAP server and retrieve enrolment
information.


.. sidebar:: License Aside

  One of the reasons for implementing external feeds as small scripts with
  a defined interface is that they are not bound by the AGPL license
  that OASIS comes under, and do not have to be written in Python.
  This allows you to link OASIS to non open-source systems.

.. image:: admin_feeds_example.png
  :width: 400px


Working examples are included to cover several common cases,
but you can add your own. If you name them local_SOMETHING,
they will not be accidentally overwritten by future OASIS upgrades.

You can have different feeds connecting to different systems if you wish.
There are currently two supported types of feed:

Group Feeds
^^^^^^^^^^^

Group Feed scripts tell OASIS how users are arranged into groups. For example: students
enrolled in courses, or groups of tutors.

When run, the feed scripts should output a one line status code followed by a simple list of usernames, one per line::

  OK
  ccog001
  fsmi324
  jblo034



If the feed encounters an error, it should output a one line ERROR code, followed
by a human readable error message, for example::

  ERROR
  This feed script was unable to contact
  the LDAP server, please see the server
  log for details.


OASIS will report these errors (if any) in the Server Administration feeds pages of the
application.

Look at the files in the OASIS `deploy/feeds <https://github.com/colincoghill/oasisqe/tree/master/deploy/feeds>`_ folder for some example scripts.

User Account Feeds
^^^^^^^^^^^^^^^^^^

User Account feeds tell OASIS how to find details on users with non-OASIS accounts.

For example when "fjon032" logs in for the first time, OASIS may run the User
Account Feed scripts and expect one of them to return the user's full name and
email address::

  uname: fjon032
  fullname: Freddie Jones
  email: f.jones@example.com

It may periodically re-run these daily to pick up any updates to the user's details.


No Feeds
^^^^^^^^

It is entirely possible to run OASIS as a standalone system, without configuring any feeds. It
will look after its own user accounts and groups. However, feeds allow you to integrate OASIS
with other systems which may already look after accounts and groups for you.


