oasisqe
=======

OASIS Question Engine

Current Status:  "In Development, a few days from the first release"

The "OASIS" Online Assessment system was developed by The University of Auckland, New Zealand, to assist
in the teaching of large undergraduate engineering courses. The original system began in 1998, but it
has been updated over time. We gained permission to release the code as Open Source, but lacked the
resources to do so properly. Several other groups have taken the OASIS code to try it themselves, 
however.

In 2012 it became clear that the code needed some work - it is still very successful and we've still
been unable to find anything else that does its job - to bring it up to modern security standards, with
a more palatable look and feel.

I have taken the OASIS v3.6 code base, developed mostly in 2001-2004 (by me), and gone through, removing old
components, refreshing the look and feel, and fixing security issues. This has been a major piece
of work, requiring a rewrite of approximately 1/3 of the code.

The plan is to release this code as a series of OSS releases, as I get enough features of the original
system active to be useful to other people.

This code has been developed mostly under the auspices of The University of Auckland, and is used 
successfully by us. The University does not, however, otherwise endorse it or commit to any support
of other users.

Feel free to download the software, as it is, and try it out. If you find it useful, use it! If you
have any suggestions or improvements, feel free to contact me.

Colin Coghill
 ( colin@colincoghill.com )
 




Things still To Do
------------------

3.9.1 OSS Release
=================

Focus: A useful practice system

Accounts:
 * Change password
 * Enrol in (open) course
 * Forgotten password process
 * User account management from Course Admin section
 * Way to delete/deactivate an account

Management
 * Scheduled task runner/monitor - stats, enrolment, etc
 * Better error checking or handling of permissions on log file & cache

Install:
 * Install guide
 * Make sure sample configs etc work
 * Landing page - do a nice welcome/introduction page
 * Create fresh empty schema for new installs
 * Turn off assertion checking in production
 * OaPool's postgres pool size - revisit for running under wsgi
 * Question Creation Documentation
 * Credits, Stephane's number stuff. Davy's editor. Nilroy's theme.
 * Web site
 * Check Licensing, especially on 3rd party components, fonts
 * Make sure appropriate license documents are included

Testing:
 * Test visibility of topics/questions to unenrolled but valid accounts.
 * Test all links on all pages.
 * Check stats are correct when starting from empty db.
 * Walk through installation from fresh start, check stats, adding courses, etc.


3.9.2 OSS Release
=================

Focus:   Integration with external auth/enrolment information

 * Configurable login page
 * Use Apache web server for auth
 * Use uploadable spreadsheets, or spreadsheets in a nominated location for class lists


3.9.3 OSS Release
=================

Focus: Assessment


The assessment section has been mostly brought over from the previous system, but a few minor bugs still remain and it needs more testing.

Assessment edit:
 * start/end times give odd error messages sometimes.
 * Can create assessment with blank question - causes error when it's started

Assess:
 * autosave isn't
 * Make sure assessment timer is good
 * view assessment results!


3.9.4 OSS Release
=================

Focus:  Question Editing

 * The "numeric question editor" has not yet been brought over from the previous system, and it has a few serious bugs.

Fix and re-enable Numeric Question Editor
 * Integrate with 3.8
 * Question renaming
 * Large and small numbers



4.0  OSS Release
================

Focus:  Finish moving/implementing functionality of 3.6 OASIS

 * LDAP integration.
 * Check and enable "How am I doing?" Practice section
 * Simple multi-choice Question Editor
 * Messages editable in UI again






Future - 4.1?
----
 * SSO support (Shibboleth?)
 * Database cleanup script.
 * Course/semester codes need to be redone every semester. Cope a lot better with historical enrolment data.
 * Assessment question weighting
 * Statistics on assessment
 * More Statistics on questions
 * Cleanup logging - only error log stuff that needs to be fixed, maybe have separate debug logs
