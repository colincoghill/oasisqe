#!/bin/bash

# Provisions an Ubuntu (Trusty) VM to run OASIS with a useful "developer" configuration.
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

adduser --disabled-login --disabled-password --gecos OASIS oasisqe

DBPASS=`uuidgen`

su postgres -c "psql postgres <<EOF
  create user oasisqe;
  alter user oasisqe with password '${DBPASS}';
EOF"

su postgres  -c "createdb -O oasisqe oasisqe"
su oasisqe -c "psql -Uoasisqe -W oasisqe -f /opt/oasisqe/3.9/deploy/emptyschema_394.sql"

mkdir -p /var/cache/oasisqe/v3.9
chown oasisqe /var/cache/oasisqe
mkdir -p /var/log/oasisqe
chown oasisqe /var/log/oasisqe

cp /opt/oasisqe/3.9/deploy/sampleconfig.ini /etc/oasisqe.ini
sed -i "s/pass: SECRET/pass: ${DBPASS}/g" /etc/oasisqe.ini
sed -i "s/statichost: http:\/\/localhost/statichost: http:\/\/localhost:8080/g" /etc/oasisqe.ini

cp /opt/oasisqe/3.9/deploy/apache24config.sample /etc/apache2/sites-available/oasisqe.conf
a2ensite oasisqe

service apache2 reload

