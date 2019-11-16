#!/bin/bash
set -eu

# Install the system dependencies needed by OASIS
#

date > /tmp/provision.notes
echo "Installing dependencies for OASIS on Ubuntu Bionic" >> /tmp/provision.notes

APTOPTS=-y
export DEBIAN_FRONTEND=noninteractive

# pre-answer interactive configuration for Postfix
debconf-set-selections <<< "postfix postfix/mailname string local.dev"
debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'"

# Remove repos we don't need
sed -i '/bionic-backports/{s/^/#/}' /etc/apt/sources.list
sed -i '/deb-src/{s/^/#/}' /etc/apt/sources.list

apt-get update
apt-get upgrade ${APTOPTS}

# Apache
apt-get install ${APTOPTS} apache2 libapache2-mod-wsgi

# PostgreSQL
apt-get install ${APTOPTS} postgresql postgresql-client

# Mail and memcached
apt-get install ${APTOPTS} postfix unzip memcached

# generate secure passwords
apt-get install ${APTOPTS} pwgen

# We'd prefer these by pip, but they like to compile stuff during install so need lots of dev things installed.
apt-get install ${APTOPTS} python-psycopg2 python-bcrypt python-lxml python-pillow python-ldap

# Ubuntu pip is a bit old, but installing it means we can use it to install a newer one
apt-get install ${APTOPTS} --no-install-recommends python-pip

# Upgrade pip
pip install --upgrade pip

# otherwise bash gives us the previous version
hash -r

pip install --upgrade setuptools

pip install pipenv

echo "Ubuntu Bionic System Dependencies installed"
