#!/bin/bash

# Sets up Ubuntu (Xenial) to run OASIS with a useful "developer" configuration.
#
# Assumes oasis code is mounted at /opt/oasisqe/3.9  (Vagrant should do this)
# This is not appropriate for running a production site. It may be insecure.
#
# ToDo: allow this to run multiple times. ie. check things before doing them

date > /tmp/provision.notes
echo "Provisioning OASISDEV" >> /tmp/provision.notes

BASEDIR=/opt/oasisqe/3.9
LOGDIR=/var/log/oasisqe


APTOPTS=-y

# pre-answer interactive configuration for Postfix
debconf-set-selections <<< "postfix postfix/mailname string local.dev"
debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'"

# Remove repos we don't need
sed -i '/xenial-backports/{s/^/#/}' /etc/apt/sources.list
sed -i '/deb-src/{s/^/#/}' /etc/apt/sources.list

cd ${BASEDIR}

apt-get update
apt-get upgrade

# Apache
apt-get install ${APTOPTS} apache2 libapache2-mod-wsgi

# PostgreSQL
apt-get install ${APTOPTS} postgresql postgresql-client

# Mail and memcached
apt-get install ${APTOPTS} postfix unzip memcached

# We'd prefer these by pip, but they like to compile stuff during install so need lots of dev things installed.
apt-get install ${APTOPTS} python-psycopg2 python-bcrypt python-lxml python-pillow

# Ubuntu pip is a bit old, but installing it means we can use it to install a newer one
apt-get install ${APTOPTS} --no-install-recommends python-pip

# Upgrade pip
pip install --upgrade pip
pip install --upgrade setuptools

# Install OASIS python requirements
pip install -r src/requirements.txt
# Install extra requirements for development/testing
pip install -r src/requirements-dev.txt

adduser --disabled-login --disabled-password --gecos OASIS oasisqe

DBPASS=`uuidgen`

mkdir -p ${LOGDIR}
chown oasisqe ${LOGDIR}
touch ${LOGDIR}/main.log
chown oasisqe ${LOGDIR}/main.log

cp ${BASEDIR}/deploy/sampleconfig.ini /etc/oasisqe.ini
sed -i "s/pass: SECRET/pass: ${DBPASS}/g" /etc/oasisqe.ini
sed -i "s/statichost: http:\/\/localhost/statichost: http:\/\/localhost:8082/g" /etc/oasisqe.ini
sed -i "s/url: http:\/\/localhost\/oasis/url: http:\/\/localhost:8082\/oasis/g" /etc/oasisqe.ini

su postgres -c "psql postgres <<EOF
  create user oasisqe;
  alter user oasisqe with password '${DBPASS}';
EOF"

su postgres  -c "createdb -O oasisqe oasisqe"
su oasisqe -c "/opt/oasisqe/3.9/bin/oasisdb init"

cp ${BASEDIR}/deploy/apache24config.sample /etc/apache2/sites-available/oasisqe.conf
a2ensite oasisqe

service apache2 reload

su oasisqe -c "${BASEDIR}/bin/create_test_topic EXAMPLE101 Samples"
echo
echo 
echo OASISQE deployed to http://localhost:8082/oasis
echo
echo "********************************************"
su oasisqe -c "${BASEDIR}/bin/reset_admin_password devtest"
echo "********************************************"
