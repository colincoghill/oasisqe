#!/bin/bash

# Sets up Ubuntu (Xenial) to build OASIS
#
# We want to install a minimal clean system then let pip and compiler do their
# stuff to produce a directory full of stuff that, hopefully, works on other
# people's Xenial installs.


APTOPTS=-y

cd ${BASEDIR}
VERSION=`git describe --tags` 

apt-get update
apt-get upgrade

# PostgreSQL
apt-get install ${APTOPTS} postgresql-client git make memcached

# Ubuntu pip is a bit old, but installing it means we can use it to install a newer one
apt-get install ${APTOPTS} --no-install-recommends python-pip

# upgrade pip, xenial version is a bit old
pip install -U pip
