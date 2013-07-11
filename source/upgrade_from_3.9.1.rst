..

Upgrade from OASIS 3.9.1 to 3.9.3
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

1. There are a few new configuration options. Edit the OASIS configuration file::


    nano /etc/oasisqe.ini


New Options (with defaults)::

    [web]

    # The page to present by default.  "landing" or "locallogin" or "webauth"
    default: landing

    # Allow people to log in using local OASIS accounts.
    enable_local_login: True

    # Allow people to log in using accounts from external systems (via feeds)
    enable_webauth_login: True

    # Present a contact URL instead of email address. (optional)
    contact_url:  http://www.example.com/

    # Location of template files which will override OASIS own pages so you
    # can customise the look/branding. Currently only does landing_page.html
    theme_path: /var/lib/oasisqe/themes/ece

    [app]

    #  location for scripts that handle feeds (eg. enrolment)
    feed_path: /var/lib/oasisqe/feeds


These are described as follows:

Authentication
^^^^^^^^^^^^^^

OASIS 3.9.3 adds support for authenticating users against external systems, for
example an Active Directory. A few new configuration options have been added

*default*

   Since OASIS supports several ways of logging in, you can configure which the
   user is presented with when they go to the home URL.

   landing:
       A welcome page that displays buttons with links to enabled login methods.

   locallogin:
       A login screen asking the user for their name and password. These will be checked against OASIS own user account database.

   webauth:
       The user will be redirected to a URL that should, if the web server is configured correctly, require them to authenticate using an external system.


*enable_local_login*
*enable_webauth_login*

   Allow users to log in using local or webauth login. You can have one or the other, or both enabled.

   NOTE: If local login is disabled, the "admin" account will not be able to log in. In this case you could promote an
   external user account to have sysadmin status. The recommended action is to leave local login enabled, but disable
   open_registration, and do not link to the page. Admin can go directly to it at::

      https://HOST/oasis/login/local


*contact_url*

    Will provide a contact URL instead of a contact email address. This is useful for,
    for example, linking to a ticket system.


*theme_path*

    If you copy "landing_page.html" from src/templates to this folder, OASIS will load
    your copy instead of its own. Use this to customize the front landing page so it
    won't be overwritten during the next OASIS upgrade. This is the only file that
    is treated this way at the moment. We're still investigating the best way to handle
    "theming/branding" for the future.


Feeds
^^^^^

The way OASIS implements connecting to external systems for user information is through "feeds". These
are described in :doc:`admin_feeds`

*feed_path*
   The folder that the scripts/plugins that implement connecting to external systems should go. This should
   be empty by default, you will then copy appropriate scripts in.




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
      --oasis-ver=X.Y.Z   work with a specific OASIS version. (default 3.9.3)
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
        migrate             - Migrate data from another OASIS installation.

You can ask it to look at your database and report the status::

    ./oasisdb status

    Connecting to database:
    host:  engdbprd02.foe.auckland.ac.nz
    database:  oasisdb
    username:  oasisdb

    There is already an OASIS database here.
    Detected DB Version 3.9.1

    68699 user records
    3075 question templates
    219 assessments
    Contains non-default data.
    It contains data, please be SURE you have the correct database
    settings and wish to erase the existing data
    before using the   --erase-existing   option.


In this case it's telling us there's a 3.9.1 database.

To upgrade it we use the *uprade* option::

    ./oasisdb upgrade
    Migrated table structure from 3.9.1 to 3.9.2
    Migrated table structure from 3.9.1 to 3.9.3


Done
^^^^

If all went well, we should now have an OASIS v3.9.3 installation running. Remember
to restart Apache::

    service apache2 restart

And you should be able to log in to OASIS and access the new features.

