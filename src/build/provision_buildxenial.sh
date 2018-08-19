#!/bin/bash
set -eu

# Sets OASIS up on Ubuntu (Xenial) with default config and all dependencies.
#
# Assumes oasis code is mounted at /opt/oasisqe/src  (Vagrant should do this)
#
# will produce a pipenv in /opt/oasisqe/3.9 with all the python dependencies included
#
# ToDo: allow this to run multiple times. ie. check things before doing them

date > /tmp/provision.notes
echo "Building OASIS on Xenial" >> /tmp/provision.notes

export SRC=/opt/oasisqe/src
export DEST=/opt/oasisqe/3.9

mkdir -p ${DEST}/bin
cd ${DEST}

BINDIR=${DEST}/bin
OASISLIB=${DEST}

/bin/bash ${SRC}/src/build/install_systemdeps_xenial.sh
/bin/bash ${SRC}/src/build/setup_build_pythonenv.sh

echo "Configuring for Build"

adduser --disabled-login --disabled-password --gecos OASIS oasisqe

DBPASS=`pwgen 16`

mkdir -p "${DEST}/config"

cp ${SRC}/docs/examples/sampleconfig.ini ${DEST}/config/oasisqe.ini
sed -i "s/pass: SECRET/pass: ${DBPASS}/g" ${DEST}/config/oasisqe.ini
sed -i "s/statichost: http:\/\/localhost/statichost: http:\/\/localhost/g" ${DEST}/config/oasisqe.ini
sed -i "s/url: http:\/\/localhost\/oasis/url: http:\/\/localhost\/oasis/g" ${DEST}/config/oasisqe.ini

cp ${SRC}/docs/examples/apache24config.sample ${DEST}/config/oasisqe-apache.conf
echo
echo OASISQE build deployed to ${DEST}
echo with default config in ${DEST}/config
echo
echo "********************************************"
