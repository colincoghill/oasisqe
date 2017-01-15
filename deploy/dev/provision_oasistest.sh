#!/bin/bash

# Sets up Ubuntu (Trusty) or Debian (Jessie) to run OASIS with a useful "test" configuration.
#
# Assumes oasis code is mounted at /opt/oasisqe/3.9  (Vagrant should do this)
# This is not appropriate for running a production site. It may be insecure.
#
# Note: this will trash databases, don't give it creds to your production database!

date > /tmp/provision.notes
echo "Provisioning OASISTEST" >> /tmp/provision.notes

APTOPTS=-y

apt-get update
apt-get upgrade
apt-get install ${APTOPTS} apache2 libapache2-mod-wsgi memcached
apt-get install ${APTOPTS} python-bcrypt python-decorator python-flask python-imaging python-jinja2
apt-get install ${APTOPTS} python-memcache python-psycopg2 python-openpyxl
apt-get install ${APTOPTS} postgresql postgresql-client unzip
apt-get install ${APTOPTS} --no-install-recommends python-pip
apt-get install ${APTOPTS} python-nose2 python-coverage
pip install Flask-WTF

adduser --disabled-login --disabled-password --gecos OASIS oasisqe

DBPASS=oasistest

mkdir -p /var/log/oasisqe
chown oasisqe /var/log/oasisqe
touch /var/log/oasisqe/main.log
chown oasisqe /var/log/oasisqe/main.log

cp /opt/oasisqe/3.9/deploy/dev/testconfig.ini /etc/oasisqe.ini
sed -i "s/pass: SECRET/pass: ${DBPASS}/g" /etc/oasisqe.ini
sed -i "s/statichost: http:\/\/localhost/statichost: http:\/\/localhost:8081/g" /etc/oasisqe.ini
sed -i "s/url: http:\/\/localhost\/oasis/url: http:\/\/localhost:8081\/oasis/g" /etc/oasisqe.ini

su postgres -c "psql postgres <<EOF
  create user oasisqe;
  alter user oasisqe with password '${DBPASS}';
EOF"

su postgres  -c "createdb -O oasisqe oasistest"
su oasisqe -c "/opt/oasisqe/3.9/bin/oasisdb init"

cp /opt/oasisqe/3.9/deploy/apache24config.sample /etc/apache2/sites-available/oasisqe.conf
a2ensite oasisqe

service apache2 reload

echo
echo 
echo OASISTEST deployed to http://localhost:8081/oasis
echo
echo ********************************************
su oasisqe -c "/opt/oasisqe/3.9/bin/reset_admin_password oasistest"
echo ********************************************
