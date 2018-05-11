#!/bin/bash

# Sets up Ubuntu (Xenial) to run OASIS
#
# At the moment we need to install some dependencies, but eventually
# aim to have it packaged as a .deb  that does that automatically


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

sudo mkdir -p /opt/oasisqe
