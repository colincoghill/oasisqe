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