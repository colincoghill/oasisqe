..

Install on Debian Linux 7 (Wheezy)
==================================


Mostly the same as Ubuntu, except we need to do something different to get python-bcrypt


Single Machine Install
----------------------


#. Install a basic Debian Linux system.

   Available from http://www.debian.org/

   32/64 bits doesn't matter. 64bit is probably recommended for a server unless you're low on RAM, in which
   case 32 might be slightly more compact.

   Go with defaults unless you need something else.


#. Install dependencies

    **as the root user**::

        apt-get install apache2 libapache2-mod-wsgi memcached
        apt-get install python-decorator python-flask python-imaging python-jinja2
        apt-get install python-memcache python-psycopg2 python-openpyxl python-pip
        apt-get install postgresql-9.1 postgresql-client-9.1
        apt-get install python-dev
        pip install bcrypt


#. Create an account for OASIS to run under.

    When prompted for a Full Name, "OASIS Web Application" will do::

        adduser --disabled-login --disabled-password oasisqe


#. Setup the main OASIS code

    It is possible to install OASIS elsewhere if you like, you will have to change the paths in various configuration
    options later::

        mkdir -p /opt/oasisqe
        cd /opt/oasisqe
        wget http://www.oasisqe.com/downloads/oasis3.9_latest.tgz
        tar -zxf oasis3.9_latest.tgz


#. Set up the OASIS database

    Choose a password for the database. You will not have to type this in often, it will go in configuration
    scripts, so pick something quite complex and secure. "createuser" will prompt you for this password.
    The database user does not need to be a superuser or to create new roles::

        su postgres
        createuser oasisdb -d -l -P
        createdb -O oasisdb oasisdb
        psql -Uoasisdb -h localhost -W oasisdb < /opt/oasisqe/3.9/deploy/emptyschema.sql


#. Setup OASIS working space and logs

    **as the 'root' user again**::

        mkdir -p /var/cache/oasisqe/3.9
        chown oasisqe /var/cache/oasisqe
        mkdir /var/log/oasisqe
        chown oasisqe /var/log/oasisqe


#. Setup the main OASIS configuration file

    You can use VI or some other editor instead of nano, if you like. Go through the file and fill in the various
    values appropriately. The main ones you will need to change are the email addresses, the database password, and the URL.
    Most of the other defaults are fine::

        cp /opt/oasisqe/3.9/deploy/sampleconfig.ini /etc/oasisqe.ini
        nano /etc/oasisqe.ini


#. Setup Apache to serve OASIS.

    This configuration file tells Apache where to find the (default) OASIS install::

        cp /opt/oasisqe/3.9/deploy/apacheconfig.sample /etc/apache2/sites-available/oasisqe
        a2ensite oasisqe

    If you have changed any of the paths in the OASIS configuration file, you may need to also
    change them in the apache confiration file::

        nano /etc/apache2/sites-available/oasisqe


#. Restart Apache.

    Ask Apache to reload its configuration::

        service apache2 reload

    OASIS should now be available at the URL you configured.

#. Reset the Admin password

    If you forget it you can perform this step again and it will reset it again::

        /opt/oasisqe/3.9/bin/reset_admin_password


    You should now be able to log in as the user "admin", with the password given to you above.


#. Setup daily schedule

    OASIS needs a daily task to run that does things like updates statistics::

        crontab -e -u oasisqe

    add the line::

        # m h  dom mon dow   command
        0 7 * * * /opt/oasisqe/3.9/bin/run_daily

    This will run the task at 5am every morning. You can choose another time if you wish.


Troubleshooting
---------------

    Apache errors (Internal Server Error 500) should show up in::

        /var/log/apache2/error.log



