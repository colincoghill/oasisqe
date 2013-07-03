.. OASIS QE documentation master file, created by


"UofA" Installation
====================

This section will walk through the installation of OASIS at an un-named university.

Need to know
^^^^^^^^^^^^
  * The URL the site will run on
  * The e-mail address of the person providing desktop support for OASIS
  * The e-mail address of the systems administrator responsible for OASIS
  * The address of an SMTP server OASIS can use to send email
  * How to link our web server to the existing university systems for authentication.
  * How to retrieve account details and enrolment information from the university systems.

In this case for the site we'll use the URL:
  http://www.oasisqe.com/uofa
and email:
  uofa@oasisqe.com
our local SMTP server is at:  smtp.oasisqe.com

In this example our external system allows user details to be looked up by
an LDAP server. Password authentication is managed by the Kerberos service, which
is supported by the Apache web server.
Group memberships come from a

We will need to install the extra packages for Python LDAP support for the OASIS
LDAP scripts::

    apt-get install python-ldap

The university already has a PostgreSQL database server, so we'll make use
of that instead of installing our own one.


Install and Configure
^^^^^^^^^^^^^^^^^^^^^

On the web application server we will need to change some things in the OASIS configuration file::

   nano /etc/oasisqe.ini


First, the web interface. We need to tell OASIS our URL::

   [web]
   url: https://www.oasisqe.com/uofa
   statichost: https://www.oasisqe.com
   staticpath: uofa

And the contact e-mail address to display on the web interface::

   email: uofa@oasisqe.com


Don't allow new people to sign themselves up and create accounts::

   open_registration: False

Instead, we want to use the web server's authentication. This will not present
a login page, but will instead request authentication information from the web
server::

   default: webauth


Information about the application comes next::

   [app]

   homedir: /opt/oasisqe/3.9/src
   logfile: /var/log/oasisqe/main.log

The *secretkey* is an important security measure. It protects users from being
able to log in as each other, among other things. We must change it to something
random and secret (use your own)::

   secretkey: t9Yptn0YjnSSmRafe0KF5F8Cyz3bUw

Since there's just one administrator, when the system generates serious errors,
the email address to send them to will be the same as above::

   email_admins: uofa@oasisqe.com

Tell OASIS to send email via the organization's mail server::

   smtp_server: mail.oasisqe.com

We need to use external "feeds" to link to the enrolment system::

   #  location for scripts that handle feeds (eg. enrolment)
   feed_path: /var/lib/oasisqe/feeds

Fill in the credentials and host information for our PostgreSQL database::

   [db]

   host: dbserver.oasisqe.com
   dbname: oasisdb
   uname: oasisdb
   pass: SECRET
   port: 5432

As will the cache settings::

   [cache]

   cachedir: /var/cache/oasisqe/v3.9
   memcache_enable: True


Any time we make changes to this configuration file, we must tell Apache
to restart OASIS::

Authentication
^^^^^^^^^^^^^^

When users log in to OASIS we want our web server to authenticate them, not
OASIS itself. We can do this by configuring the web server, in this case Apache,
to pass the credentials to OASIS:

  .. image:: example_uofa_diagram1.png
    :width: 600px

In this case our system already has Kerberos configured, we just need to
tell Apache when to apply it::

  nano /etc/apache2/sites-available/oasisqe

Our Apache is already configured to connect to our Kerberos service for authentication::

    KrbAuthoritative on
    KrbAuthRealms OASISQE.COM
    KrbMethodK5Passwd On
    KrbMethodNegotiate off
    KrbVerifyKDC off
    KrbDelegateBasic Off

(If you also need to set up Apache for Kerberos support, we use http://modauthkerb.sourceforge.net/ ,
but there may be other methods, eg. if you're using IIS it can probably use the AD equivalent)

Add a section to tell Apache that it is to perform authentication for OASIS::

      <Directory /oasis/login/webauth/submit>
                AllowOverride All
                Order allow,deny
                allow from all
                AuthType Kerberos
                AuthName "Netaccount Login"
                require valid-user
      </Directory>

Now when the user goes to OASIS, if it doesn't know who they are, it will redirect
them to /oasis/login/webauth. Apache will then prompt them for username and password
and, if correct, will provide the username to OASIS. When OASIS encounters a
username it has not seen before, it will fill in some default details (mostly
blank) and then see if it can look them up using a User Feed script.

Any time you change the OASIS or Apache configuration files, restart Apache::

  service apache2 restart

Check it Works
^^^^^^^^^^^^^^

Now we can log in to OASIS and verify that it all works:

We open a web browser and go to the URL: https://www.oasisqe.com/uofa
(obviously, using our own URL here). Log in using your credentials from the
central system.


Create a Course
^^^^^^^^^^^^^^^

