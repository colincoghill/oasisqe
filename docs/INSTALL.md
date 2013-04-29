
Installation Guide
==================

Work in progress, should not be published or used yet.


Ubuntu Linux 12.04
------------------

Single Machine Install


1. Install a basic Ubuntu 12.04 Linux system.
   If you have a newer version it should work fine, but hasn't specifically been tested yet, let us know!


2. Install dependencies
   as root

   `apt-get install apache2 libapache2-mod-wsgi memcached`

   `apt-get install python-bcrypt python-decorator python-flask python-imaging python-jinja2`
   `apt-get install python-memcache python-psycopg2 python-openpyxl`

   `apt-get install postgresql-9.1 postgresql-client-9.1`


3. Create an account for OASIS to run under

   `adduser --disabled-login --disabled-password oasisqe`


4. Setup the main OASIS code

   It is possible to install OASIS elsewhere if you like, you will have to change the paths in various configuration
   options later

   `mkdir /opt/oasisqe`
   `cd /opt/oasisqe`
   `tar -zxf OASIS_3.9.tgz`


5. Set up the OASIS database
    Choose a password for the database. You will not have to type this in often, it will go in configuration
    scripts, so pick something quite complex and secure. "createuser" will prompt you for this password.

    `su postgres`
    `createuser oasisdb -d -l -P `
    `createdb -O oasisdb oasisdb`
    `psql -Uoasisdb oasisdb < /opt/oasisqe/3.9/deploy/emptyschema.sql`

6. Setup the main OASIS configuration file

   `cp 3.9/deploy/sample_config.ini /etc/oasis4.ini`
   `nano /etc/oasis4.ini`

You can use VI or some other editor instead of nano, if you like. Go through the file and fill in the various
values appropriately.
