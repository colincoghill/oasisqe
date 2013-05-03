The main priority for the near future is to reach feature parity with the old version that the University of
Auckland has used successfully for years. Much of the code is in place but many parts are disabled until they
can be tested to my satisfaction.

When it has reached this goal, I'll label it "Version 4.0" and do a more complete release, packaged for
various distributions, etc.

The 3.9.x releases should be perfectly usable in their own way though, just missing features or documentation.


3.9.2 OSS Release
=================

Focus:   Integration with external auth/enrolment information. User account/class management.


Install:
 * Configurable login page
 * Use Apache web server for auth
 * Use uploadable spreadsheets, or spreadsheets in a nominated location for class lists
 * Enrol in (open) course
 * User account management from Course Admin section
 * Way to delete/deactivate an account
 * 
 * Better error checking or handling of permissions on log file & cache
 * Scheduled task runner/monitor - stats, enrolment, etc

Testing:
 * Test visibility of topics/questions to unenrolled but valid accounts.
 * Check stats are correct when starting from empty db.

Documentation

 * Basic usage guide
 * Landing page - do a nice welcome/introduction page
 * Basic Question Creation Documentation
 * Basic admin guide


3.9.3 OSS Release
=================

Focus: Assessment

The assessment section has been mostly brought over from the previous system, but a few minor 
bugs still remain and it needs more testing.

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

 * The "numeric question editor" has not yet been brought over from the previous system, 
   and it has a few serious bugs.

Fix and re-enable Numeric Question Editor
 * Integrate with 3.8
 * Question renaming
 * Large and small numbers

Documentation

* Credits, Stephane's number stuff. Davy's editor. Nilroy's theme.
* Support Web site



4.0  OSS Release
================

Focus:  Finish moving/implementing functionality of 3.6 OASIS

 * LDAP integration.
 * Check and enable "How am I doing?" Practice section
 * Simple multi-choice Question Editor
 * Manuals






Future - 4.1?
----
 * SSO support (Shibboleth?)
 * Database cleanup script.
 * Course/semester codes need to be redone every semester. Cope a lot better with historical enrolment data.
 * Assessment question weighting
 * Statistics on assessment
 * More Statistics on questions
 * Cleanup logging - only error log stuff that needs to be fixed, maybe have separate debug logs
