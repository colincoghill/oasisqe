Installation Guide
==================

 * Ubuntu Linux 12.04.2
 * Debian Linux 7 (scroll down)


Ubuntu Linux 12.04.2
------------------

Single Machine Install


1. Install a basic Ubuntu 12.04.2 "Server" Linux system.
   Available from http://www.ubuntu.com/download

   If you have a newer version it should work fine, but hasn't specifically been tested yet, let us know!
   32/64 bits doesn't matter. 64bit is probably recommended for a server unless you're low on RAM, in which
   case 32 might be slightly more compact.

   Don't install any extras unless you need them for something else. OpenSSH Server is a good idea for
   remote management.

2. Install dependencies
   as root
```Shell
    apt-get install apache2 libapache2-mod-wsgi memcached
    apt-get install python-bcrypt python-decorator python-flask python-imaging python-jinja2
    apt-get install python-memcache python-psycopg2 python-openpyxl
    apt-get install postgresql-9.1 postgresql-client-9.1
```

3. Create an account for OASIS to run under
```Shell
    adduser --disabled-login --disabled-password oasisqe
```
   When prompted for a Full Name, "OASIS Web Application" will do.

4. Setup the main OASIS code

   It is possible to install OASIS elsewhere if you like, you will have to change the paths in various configuration
   options later
```Shell
    mkdir -p /opt/oasisqe
    cd /opt/oasisqe
    wget http://www.oasisqe.com/downloads/oasis3.9_latest.tgz
    tar -zxf oasis3.9_latest.tgz
```

5. Set up the OASIS database
    Choose a password for the database. You will not have to type this in often, it will go in configuration
    scripts, so pick something quite complex and secure. "createuser" will prompt you for this password.
    The database user does not need to be a superuser or to create new roles.
```Shell
     su postgres
     createuser oasisdb -d -l -P
     createdb -O oasisdb oasisdb
     psql -Uoasisdb -h localhost -W oasisdb < /opt/oasisqe/3.9/deploy/emptyschema.sql
```

6. Setup OASIS working space and logs.
   (as the 'root' user again)
```Shell
    mkdir -p /var/cache/oasisqe/v3.9
    chown oasisqe /var/cache/oasisqe
    mkdir /var/log/oasisqe
    chown oasisqe /var/log/oasisqe
```

7. Setup the main OASIS configuration file
```Shell
    cp /opt/oasisqe/3.9/deploy/sampleconfig.ini /etc/oasisqe.ini
    nano /etc/oasisqe.ini
```
You can use VI or some other editor instead of nano, if you like. Go through the file and fill in the various
values appropriately. The main ones you will need to change are the email addresses, the database password, and the URL.
Most of the other defaults are fine.

If you are running in a Virtual Machine, you may need to change the URL and the static URL in the
configuration file to be the IP address of your Virtual Machine.

8. Setup Apache to serve OASIS
```Shell
    cp /opt/oasisqe/3.9/deploy/apacheconfig.sample /etc/apache2/sites-available/oasisqe
    a2ensite oasisqe
```

9. Restart Apache
```Shell
    service apache2 reload
```

    OASIS should now be available at the URL you configured.

10. Reset the OASIS Admin password
   If you forget it you can perform this step again and it will reset it again.
```Shell
    /opt/oasisqe/3.9/bin/reset_admin_password
```
   You should now be able to log in as the user "admin", with the password given to you above.

11. Setup daily schedule
    OASIS needs a daily task to run that does things like updates statistics.
```
    crontab -e -u oasisqe
```
    add the line:

```Shell
    # m h  dom mon dow   command

    0 7 * * * /opt/oasisqe/3.9/bin/run_daily
```
    This will run the task at 5am every morning. You can choose another time if you wish.


Troubleshooting
---------------

Apache errors (Internal Server Error 500) should show up in
```
   /var/log/apache2/error.log
```



Debian Linux 7 (Wheezy)
-----------------------
Tested on Release Candidate 2

Mostly the same as Ubuntu, except we need to do something different to get python-bcrypt



Single Machine Install


1. Install a basic Debian Linux system.
   Available from http://www.debian.org/

   32/64 bits doesn't matter. 64bit is probably recommended for a server unless you're low on RAM, in which
   case 32 might be slightly more compact.

   Go with defaults unless you need something else.

2. Install dependencies
   as root
```Shell
    apt-get install apache2 libapache2-mod-wsgi memcached
    apt-get install python-decorator python-flask python-imaging python-jinja2
    apt-get install python-memcache python-psycopg2 python-openpyxl python-pip
    apt-get install postgresql-9.1 postgresql-client-9.1
    apt-get install python-dev
    pip install bcrypt
```

3. Create an account for OASIS to run under
```Shell
    adduser --disabled-login --disabled-password oasisqe
```
   When prompted for a Full Name, "OASIS Web Application" will do.

4. Setup the main OASIS code

   It is possible to install OASIS elsewhere if you like, you will have to change the paths in various configuration
   options later
```Shell
    mkdir -p /opt/oasisqe
    cd /opt/oasisqe
    wget http://www.oasisqe.com/downloads/oasis3.9_latest.tgz
    tar -zxf oasis3.9_latest.tgz
```

5. Set up the OASIS database
    Choose a password for the database. You will not have to type this in often, it will go in configuration
    scripts, so pick something quite complex and secure. "createuser" will prompt you for this password.
    The database user does not need to be a superuser or to create new roles.
```Shell
     su postgres
     createuser oasisdb -d -l -P
     createdb -O oasisdb oasisdb
     psql -Uoasisdb -h localhost -W oasisdb < /opt/oasisqe/3.9/deploy/emptyschema.sql
```

6. Setup OASIS working space and logs.
   (as the 'root' user again)
```Shell
    mkdir -p /var/cache/oasisqe/v3.9
    chown oasisqe /var/cache/oasisqe
    mkdir /var/log/oasisqe
    chown oasisqe /var/log/oasisqe
```

7. Setup the main OASIS configuration file
```Shell
    cp /opt/oasisqe/3.9/deploy/sampleconfig.ini /etc/oasisqe.ini
    nano /etc/oasisqe.ini
```
You can use VI or some other editor instead of nano, if you like. Go through the file and fill in the various
values appropriately. The main ones you will need to change are the email addresses, the database password, and the URL.
Most of the other defaults are fine.

If you are running in a Virtual Machine, you may need to change the URL and the static URL in the
configuration file to be the IP address of your Virtual Machine.

8. Setup Apache to serve OASIS
```Shell
    cp /opt/oasisqe/3.9/deploy/apacheconfig.sample /etc/apache2/sites-available/oasisqe
    a2ensite oasisqe
```

9. Restart Apache
```Shell
    service apache2 reload
```

    OASIS should now be available at the URL you configured.

10. Reset the OASIS Admin password
   If you forget it you can perform this step again and it will reset it again.
```Shell
    /opt/oasisqe/3.9/bin/reset_admin_password
```
   You should now be able to log in as the user "admin", with the password given to you above.

11. Setup daily schedule
    OASIS needs a daily task to run that does things like updates statistics.
```
    crontab -e -u oasisqe
```
    add the line:

```Shell
    # m h  dom mon dow   command

    0 7 * * * /opt/oasisqe/3.9/bin/run_daily
```
    This will run the task at 5am every morning. You can choose another time if you wish.



Troubleshooting
---------------

Apache errors (Internal Server Error 500) should show up in
```
   /var/log/apache2/error.log
```




