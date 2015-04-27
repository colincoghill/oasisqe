#!/bin/bash

date > /tmp/provision.notes
echo "Provisioning OASISDEV" >> /tmp/provision.notes

APTOPTS=-y

apt-get update
apt-get upgrade
apt-get install ${APTOPTS} apache2 libapache2-mod-wsgi memcached
apt-get install ${APTOPTS} python-bcrypt python-decorator python-flask python-imaging python-jinja2
apt-get install ${APTOPTS} python-memcache python-psycopg2 python-openpyxl
apt-get install ${APTOPTS} postgresql postgresql-client


