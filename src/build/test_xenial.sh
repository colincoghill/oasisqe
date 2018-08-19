#!/bin/bash
set -eu

# Sets up Ubuntu (Xenial) to test OASIS
#
# Install it, configured for testing


APTOPTS=-y

cd ${BASEDIR}

apt-get update
apt-get upgrade

# PostgreSQL
apt-get install ${APTOPTS} postgresql-client git make memcached

# Ubuntu pip is a bit old, but installing it means we can use it to install a newer one
apt-get install ${APTOPTS} --no-install-recommends python-pip

# upgrade pip, xenial version is a bit old
pip install -U pip

mkdir -p /opt/oasisqe

cd /opt/oasisqe

tar -zxvf /home/vagrant/mnt/oasisqe-xenial.tgz

