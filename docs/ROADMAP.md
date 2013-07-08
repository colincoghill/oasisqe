The main priority for the near future is to reach feature parity with the old version that the University of
Auckland has used successfully for years. Much of the code is in place but many parts are disabled until they
can be tested to my satisfaction.

When it has reached this goal, I'll label it "Version 4.0" and do a more complete release, packaged for
various distributions, etc.

The 3.9.x releases should be perfectly usable in their own way though, just missing features or documentation.


The code is currently fairly messy - I've taken existing (working but terrible) code and gone through
replacing severely broken or insecure parts. The priority is to finish that and get the system functionally
equivalent to the old one. After that (version 4.1+) I want to seriously think about maintainance, testing,
documentation, non-Linux installs, plugins, etc, and how to get other developers involved.


3.9.3 OSS Release
=================
(This will also be the UoA release for Semester Two, 2013)

Focus:   Further integration with external auth/enrolment information. User account/class management.

The assessment section has been mostly brought over from the previous system, but a few minor
bugs still remain and it needs more testing.


Install:

 * Better error checking or handling of permissions on log file & cache

Documentation

 * Basic usage guide
 * Landing page - do a nice welcome/introduction page
 * Basic Question Creation Documentation

Assessment edit:
 * Can create assessment with blank question - causes error when it's started

Assess:
 * autosave isn't
 * Make sure assessment timer is good

Other:
 * Way to delete/deactivate an account
 * Enrol in (open) course


3.9.4 OSS Release
=================

Focus:  Question Editing

 * The "numeric question editor" has not yet been brought over from the previous system,
   and it has a few serious bugs.

Fix and re-enable Numeric Question Editor
 * Integrate with 3.9
 * Question renaming
 * Large and small numbers

Documentation

* Credits, Stephane's number stuff. Davy's editor. Nilroy's theme.
* Support Web site



3.9.5 OSS Release
=================

Focus: Loose ends

 * Permissions for groups as well as individuals
 * Example Questions
 * Simple multi-choice Question Editor
 * Check and enable "How am I doing?" Practice section


4.0  OSS Release
================

Focus:  Finish moving/implementing functionality of 3.6 OASIS

 * Manuals, documentation
 * Web site
 * Better error checking/messages
 * Cleanup logging - only error log stuff that needs to be fixed, maybe have separate debug logs
 * Upgrate/migration tools



4.1  and beyond...
==================
 * move to SQLAlchemy, or similar ORM to get all the SQL cleaned up.
 * work on tidying up the internals a bit - go more object based where possible
 * Course/semester codes need to be redone every semester. Cope a lot better with historical enrolment data.
 * Assessment question weighting
 * Themes/Branding - allow admins to change the look of the system, link with external systems better.
 * Statistics on assessment
 * More Statistics on questions
 * Database cleanup script. (clean out old practice questions)
