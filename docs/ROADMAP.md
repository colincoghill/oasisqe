The main priority for the near future is to reach feature parity with the old version that the University of
Auckland has used successfully for years. Much of the code is in place but many parts are disabled until they
can be tested to my satisfaction.

When it has reached this goal, I'll label it "Version 4.0" and do a more complete release, packaged for
various distributions, etc.

The 3.9.x releases should be perfectly usable in their own way though, just missing features or documentation.


The code is currently fairly messy - I've taken existing (working but terrible) code and gone through
replacing severely broken or insecure parts. The priority is to finish that and get the system functionally
equivalent to the old one. After that (version 4.1+) I want to seriously think about maintenance, testing,
documentation, non-Linux installs, plugins, etc, and how to get other developers involved.





4.0  OSS Release
================

Focus:  Finish moving/implementing functionality of 3.6 OASIS

 * Manuals, documentation
 * Web site
 * Better error checking/messages
 * Cleanup logging - only error log stuff that needs to be fixed, maybe have separate debug logs


4.1  and beyond...
==================
 * move to SQLAlchemy, or similar ORM to get all the SQL cleaned up.
 * work on tidying up the internals a bit - go more object based where possible

 * Themes/Branding - allow admins to change the look of the system, link with external systems better.
 * Statistics on assessment
 * More Statistics on questions
 * Database cleanup script. (clean out old practice questions)
 * Much fancier question editor
 * Revisit performance and security.
