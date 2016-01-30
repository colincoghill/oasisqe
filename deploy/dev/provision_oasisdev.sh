#!/bin/bash

# Sets up Ubuntu (Trusty) or Debian (Jessie) to run OASIS with a useful "developer" configuration.
#
# Assumes oasis code is mounted at /opt/oasisqe/3.9  (Vagrant should do this)
# This is not appropriate for running a production site. It may be insecure.
#
# ToDo: allow this to run multiple times. ie. check things before doing them

date > /tmp/provision.notes
echo "Provisioning OASISDEV" >> /tmp/provision.notes

APTOPTS=-y

apt-get update
apt-get upgrade
apt-get install ${APTOPTS} apache2 libapache2-mod-wsgi memcached
apt-get install ${APTOPTS} python-bcrypt python-decorator python-flask python-imaging python-jinja2
apt-get install ${APTOPTS} python-memcache python-psycopg2 python-openpyxl
apt-get install ${APTOPTS} postgresql postgresql-client
apt-get install ${APTOPTS} postfix unzip
apt-get install ${APTOPTS} --no-install-recommends python-pip
pip install Flask-WTF

adduser --disabled-login --disabled-password --gecos OASIS oasisqe

DBPASS=`uuidgen`

mkdir -p /var/cache/oasisqe/v3.9
chown oasisqe /var/cache/oasisqe
chown oasisqe /var/cache/oasisqe/v3.9
mkdir -p /var/log/oasisqe
chown oasisqe /var/log/oasisqe
touch /var/log/oasisqe/main.log
chown oasisqe /var/log/oasisqe/main.log

cp /opt/oasisqe/3.9/deploy/sampleconfig.ini /etc/oasisqe.ini
sed -i "s/pass: SECRET/pass: ${DBPASS}/g" /etc/oasisqe.ini
sed -i "s/statichost: http:\/\/localhost/statichost: http:\/\/localhost:8080/g" /etc/oasisqe.ini
sed -i "s/url: http:\/\/localhost\/oasis/url: http:\/\/localhost:8080\/oasis/g" /etc/oasisqe.ini

su postgres -c "psql postgres <<EOF
  create user oasisqe;
  alter user oasisqe with password '${DBPASS}';
EOF"

su postgres  -c "createdb -O oasisqe oasisqe"
su oasisqe -c "/opt/oasisqe/3.9/bin/oasisdb init"

cp /opt/oasisqe/3.9/deploy/apache24config.sample /etc/apache2/sites-available/oasisqe.conf
a2ensite oasisqe

service apache2 reload

su oasisqe -c "/opt/oasisqe/3.9/bin/create_test_topic EXAMPLE101 Samples"
echo
echo 
echo OASISQE deployed to http://localhost:8080/oasis
echo
echo ********************************************
su oasisqe -c "/opt/oasisqe/3.9/bin/reset_admin_password devtest"
echo ********************************************
