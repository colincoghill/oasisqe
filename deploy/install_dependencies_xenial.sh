#!/bin/bash

# Sets up Ubuntu (Xenial) to run OASIS
#
# Assumes oasis code is mounted at /opt/oasisqe/3.9. If this is not the case, change it here:

BASEDIR=/opt/oasisqe/3.9

LOGDIR=/var/log/oasisqe

APTOPTS=-y

cd ${BASEDIR}

apt-get update
apt-get upgrade

# Apache
apt-get install ${APTOPTS} apache2 libapache2-mod-wsgi

# PostgreSQL
apt-get install ${APTOPTS} postgresql postgresql-client

# Mail and memcached
apt-get install ${APTOPTS} unzip memcached

# We'd prefer these by pip, but they like to compile stuff during install so need lots of dev things installed.
apt-get install ${APTOPTS} python-psycopg2 python-bcrypt python-lxml python-pillow

# Ubuntu pip is a bit old, but installing it means we can use it to install a newer one
apt-get install ${APTOPTS} --no-install-recommends python-pip

# Upgrade pip
pip install --upgrade pip
pip install --upgrade setuptools

# Install OASIS python requirements
pip install -r src/requirements.txt

echo 
echo OASISQE dependencies installed
echo
