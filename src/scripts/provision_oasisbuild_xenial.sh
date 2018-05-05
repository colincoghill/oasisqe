#!/bin/bash

# Sets up Ubuntu (Xenial) to build OASIS
#
# Assumes oasis repo is mounted at /opt/oasisqe/3.9  (Vagrant should do this)
# We want to install a minimal clean system then let pip and compiler do their
# stuff to produce a directory full of stuff that, hopefully, works on other
# people's Xenial installs.

date > /tmp/provision.notes
echo "Provisioning OASISBUILD" >> /tmp/provision.notes

BASEDIR=/opt/oasisqe/3.9
OASISLIB=${BASEDIR}

APTOPTS=-y

cd ${BASEDIR}
VERSION=`git describe --tags` 

apt-get update
apt-get upgrade

# PostgreSQL
apt-get install ${APTOPTS} postgresql-client git make memcached

# Ubuntu pip is a bit old, but installing it means we can use it to install a newer one
apt-get install ${APTOPTS} --no-install-recommends python-pip


# Install OASIS python requirements
make build

# and pack it up ready for use
tar -zcvf /tmp/${VERSION}.tgz build
