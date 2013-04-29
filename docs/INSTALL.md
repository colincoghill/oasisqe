
Installation Guide
==================

Work in progress, should not be published or used yet.


Ubuntu Linux 12.04
------------------

Single Machine Install


1. Install a basic Ubuntu 12.04 Linux system.
   If you have a newer version it should work fine, but hasn't specifically been tested yet, let us know!
   32/64 bits doesn't matter. 64bit is probably recommended for a server unless you're low on RAM, in which
   case 32 might be slightly more compact.

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

4. Setup the main OASIS code

   It is possible to install OASIS elsewhere if you like, you will have to change the paths in various configuration
   options later
```Shell
    mkdir /opt/oasisqe
    cd /opt/oasisqe
    wget OASIS
    tar -zxf OASIS_3.9.tgz
```

5. Set up the OASIS database
    Choose a password for the database. You will not have to type this in often, it will go in configuration
    scripts, so pick something quite complex and secure. "createuser" will prompt you for this password.
```Shell
     su postgres
     createuser oasisdb -d -l -P
     createdb -O oasisdb oasisdb
     psql -Uoasisdb oasisdb < /opt/oasisqe/3.9/deploy/emptyschema.sql
```
6. Setup the main OASIS configuration file
```Shell
    cp /opt/oasisqe/3.9/deploy/sample_config.ini /etc/oasisqe.ini
    nano /etc/oasisqe.ini
```
You can use VI or some other editor instead of nano, if you like. Go through the file and fill in the various
values appropriately.

7. Setup Apache to serve OASIS
```Shell
    cp /opt/oasisqe/3.9/deploy/apache_config /etc/apache2/sites-available/oasisqe
    nano /etc/apache2/sites-available/oasisqe
    a2enmod oasisqe
```

8. Restart Apache
```Shell
    service apache2 restart
```

    OASIS should now be available at the URL you configured.

9. Reset the Admin password
   If you forget it you can perform this step again and it will reset it again.
```Shell
    /opt/oasisqe/3.9/bin/reset_admin_password
```
   You should now be able to log in as the user "admin", with the password given to you above.