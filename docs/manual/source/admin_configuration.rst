..

Configuration
=============


1. Most of the OASIS system configuration is in the file `/etc/oasisqe.ini`


    nano /etc/oasisqe.ini


Authentication and Login
^^^^^^^^^^^^^^^^^^^^^^^^

Authentication/Login options (with defaults)::

    [web]

    # The page to present by default.  "landing" or "locallogin" or "webauth"
    default: landing

    # Allow people to log in using local OASIS accounts.
    enable_local_login: True

    # Allow people to log in using LTI from another LMS
    enable_lti_login: False

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

These are described below:

OASIS 3.9.6 supports authenticating users against external systems, for
example an Active Directory server, or another LMS. 

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

*enable_lti_login*

   Allows users to sign-in directly to OASIS from another Learning Management System, using the LTI protocol. If you enable this,
   you will need to configure more detail from within OASIS. see :doc:`admin_lti`


Feeds
^^^^^

The way OASIS implements connecting to external systems for user information is through "feeds". These
are described in :doc:`admin_feeds`


Remember, any time you make changes to `oasisqe.ini` you will need to restart OASIS to read the new configuration. You can 
do this with::

    service apache2 restart

