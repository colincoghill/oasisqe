..

Upgrade from OASIS 3.9.2 to 3.9.3
=================================


Install
-------

1. Go to the folder OASIS is installed into::

   cd /opt/oasisqe

(or wherever you have it installed)

2. Fetch the 3.9.3 code from the download site::

   wget http://www.oasisqe.com/downloads/oasis3.9.3.tgz

3. Move the previous code out of the way::

   mv 3.9 3.9__backup

4. unpack the newest version::

   tar -zxf oasis3.9.3.tgz


Configure
---------

There are no new configuration options in 3.9.3, it's mostly a bug-fix release.


Migrate Database
----------------

There are some changes that need made to the database. These can be managed by the
included "oasisdb" tool. (described in :doc:`admin_oasisdb`

Move to the "bin" folder in OASIS and run the oasisdb tool::

   cd /opt/oasisqe/3.9/bin
   ./oasisdb

It should output some help information::

    Usage: oasisdb [--help] [--version] [command ...]

    OASIS Database Tool. It requires an already configured OASIS setup, and can be
    used to initialize or upgrade an OASIS database.

    Options:
      --version           show program's version number and exit
      -h, --help          show this help message and exit
      --erase-existing    erase any existing data first. DANGEROUS.
      --no-reset-adminpw  don't reset the admin password
      --oasis-ver=X.Y.Z   work with a specific OASIS version. (default 3.9.2)
      -v, --verbose       verbose output

    Commands:
        help                - Provide information about a specific command.
        status              - Show some status information about the database.
        show users          - List the users in the database.
        show courses        - List the courses in the database.
        resetpw             - Change the admin password.
        calcstats           - Refresh statistics calculation over whole database.

        init                - Set up the OASIS table structure in the database.
        upgrade             - Upgrade an older OASIS database to the newest version.


You can ask it to look at your database and report the status::

  Connecting to database:
  host:  localhost
  database:  oasisdb
  username:  oasisdb

  There is already an OASIS database here.
  Detected DB Version 3.9.2

  68699 user records
  3075 question templates
  219 assessments
  Contains non-default data.
  It contains data, please be SURE you have the correct database
  settings and wish to erase the existing data
  before using the   --erase-existing   option.


In this case it's telling us there's a 3.9.2 database.

To upgrade it we use the *uprade* option::

    ./oasisdb upgrade
    Migrated table structure from 3.9.2 to 3.9.3


Done
^^^^

If all went well, we should now have an OASIS v3.9.3 installation running. Remember
to restart Apache::

    service apache2 restart

And you should be able to log in to OASIS and access the new features.

