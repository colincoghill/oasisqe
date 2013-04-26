
Requirements for running OASIS
==============================

[Still notes, not formal yet]

Software
--------

OASIS has been developed to run on Ubuntu Linux. It should work on similar UNIX systems, like other Linux distributions,
 or FreeBSD, although you may have to modify the installation procedures.

It uses the PostgreSQL database. This is a free, high quality, database server. From http://www.postgresql.org/

* Ubuntu Linux 12.04
* PostgreSQL 9.0 (or newer)
* Python 2.6 or 2.7



Hardware
--------

The required hardware depends a lot on the number of users you wish to support. OASIS is reasonably efficient, and
will use multiple cores well if you have them.

We've successfully supported 2000 students (100 concurrent) using a single server with a 1GHz AMD Opteron and 1GB of RAM,
 however we were not making heavy use of some of the more advanced features of OASIS. A Quad Core 3GHz Intel server
 with 4GB of RAM should support several thousand users comfortably.

For slightly larger installations, or for ease of maintenance, a separate database server will work well.

