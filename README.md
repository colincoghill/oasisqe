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

Feel free to download the software, as it is, and try it out. If you find it useful, use it!
Right now it's mostly complete, but there are a few bugs making a fresh install somewhat error prone. I'm 
working through that at the moment, along with some sample content.

If you have any suggestions or improvements, feel free to contact me.

Colin Coghill
 ( colin@colincoghill.com )



Things still To Do
------------------
(before I consider this a usable piece of software)

3.9.1 OSS Release
=================

Focus: A useful practice system

Code:
 * Disable incomplete or inactive areas
 * A way to change the News page

Install:
 * Basic usage guide
 * Landing page - do a nice welcome/introduction page
 * OaPool's postgres pool size - revisit for running under wsgi
 * Basic Question Creation Documentation

Testing:
 * Test visibility of topics/questions to unenrolled but valid accounts.
 * Test all links on all pages.
 * Check stats are correct when starting from empty db.
 * Walk through installation from fresh start, check stats, adding courses, etc.

