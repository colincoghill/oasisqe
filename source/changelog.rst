Changelog
=========

v3.9.3
------
10th July 2013



Features
^^^^^^^^

  * Allow an optional student ID number to be included in the user feed
  * Allow an alternate (customized) landing page to be provided
  * Optional contact URL instead of email address
  * Show groups that recently expired so we can see, for example, "last semesters grades"


Bugfixes
^^^^^^^^

  * Remove link to "previous assessments" for now, it was broken.
  * If adding a permission to an unknown user, we'd Internal Server Error.
  * Topic positions were set to "None" sometimes, causing errors.
  * Hide practice topics if the user wasn't supposed to have access to them.
  * Display login message on the landing page as well as the login page
  * Fix incompatibility with openpyxl on Ubuntu 12.04
  * Restore assessment editing page
  * oasisdb tool didn't correctly identify a 3.9.2 database
  * Spreadsheet export of assessment marks wasn't working
  * Change "make sysadmin" so that browser prefetch can't trigger it by accident
  * Crash if course admin viewed a students exam that was in progress

