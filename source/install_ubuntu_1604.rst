..

Install on Ubuntu 16.04 LTS (Xenial)
=====================================

Single Machine Install
----------------------


#. Install a basic Ubuntu 16.04 "Server" Linux system.

   Available from http://www.ubuntu.com/download

   If you have a newer version it should work fine, but hasn't specifically been tested yet, let us know!
   32/64 bits doesn't matter. 64bit is recommended for a server unless you're low on RAM, in which
   case 32 might be slightly more compact.

   Don't install any extras unless you need them for something else. OpenSSH Server is a good idea for
   remote management.


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


#. Install dependencies

    **as the root user**::

        cd /opt/oasisqe/3.9
        sh deploy/install_dependencies_xenial.sh


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

        mkdir -p /var/cache/oasisqe/v3.9
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

    OASIS needs to run a daily task that does things like update statistics and
    synchronize user information with external systems::

        crontab -e -u oasisqe

    add the line::

        # m h  dom mon dow   command
        0 7 * * * /opt/oasisqe/3.9/bin/run_daily

    This will run the task at 7am every morning. You can choose another time if you wish.


Troubleshooting
---------------

    Apache errors (Internal Server Error 500) should show up in::

        /var/log/apache2/error.log



