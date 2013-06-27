..

OASIS Database Tool
-------------------

This is provided as an program in the bin/ folder of the oasisqe installation. It
provides many useful OASIS database related abilities::

  ./oasisdb

  Usage: oasisdb [--help] [--version] [command ...]

  OASIS Database Tool. It requires an already configured OASIS setup, and can be
  used to initialize or upgrade an OASIS database.

  Options:
    --version          show program's version number and exit
    -h, --help         show this help message and exit
    --erase-existing   erase any existing data first. DANGEROUS.
    --oasis-ver=X.Y.Z  work with a specific OASIS version. (default 3.9.2)
    -v, --verbose      verbose output

  Commands:
    help                - Provide information about a specific command.
    status              - Show some status information about the database.
    show users          - List the users in the database.
    show courses        - List the courses in the database.
    resetpw             - Change the admin password.
    init                - Set up the OASIS table structure in the database.
    upgrade             - Upgrade an older OASIS database to the newest version.
    migrate             - Migrate data from another OASIS installation to this one.


status
^^^^^^

The status command will have look at the configured (in /etc/oasisqe.ini) database
and display some information about it. For example::

  ./oasisdb status

  Connecting to database:
    host:  localhost
    database:  oasisdb
    username:  oasisdb

  There is already an OASIS database here.
  Detected DB Version 3.9.2

  2 user records
  0 question templates
  0 assessments

  However it does not contain much data so may be safe to erase with:
      oasisdb init --erase-existing


This is telling us that it detected a version 3.9.2 database, but that it doesn't
contain much information so is probably just a default installation.

resetpw
^^^^^^^

This will assign a new randomly generated password to the "admin" account and
display it. Use this if you have forgotten or otherwise want to change the
"admin" password. For security reasons, OASIS will not allow you to assign
an insecure password to the admin account::

  ./oasisdb resetpw
  Admin password reset to:  pirM6z32M


init
^^^^

Used when installing a fresh OASIS database. This will connect to the configured
(in oasisqe.ini) database and create the tables and data that OASIS requires to run::

  ./oasisdb init
  There is already an OASIS database here.
  Detected DB Version 3.9.2

  74 user records
  12 question templates
  3 assessments
  Contains non-default data.
  It contains data, please be SURE you have the correct database
  settings and wish to erase the existing data
  before using   the   --erase-existing   option.

If there already appears to be an existing set of tables, it may refuse unless
you also provide the --erase-existing option. WARNING: Be sure you have the
right database configured before doing so::

  ./oasisdb init --erase-existing
  There is already an OASIS database here.
  Detected DB Version 3.9.2

  74 user records
  12 question templates
  3 assessments
  Contains non-default data.
  Removing existing tables.
  Installed v3.9.2 table structure.
  Admin password reset to:  pKBNiYjbd
  Remember to restart OASIS if it's currently running.
  On Linux you can use:      sudo service apache2 restart


upgrade
^^^^^^^

This will upgrade an existing OASIS database from an earlier version. Currently
only previous 3.9.x versions are supported. This operation should be reasonably
safe, although you cannot go back to the older version, so it is recommended
that you take a backup of the database first::

  ./oasisdb upgrade
  Migrated table structure from 3.9.1 to 3.9.2
  Admin password reset to:  tE9sCb8F6


