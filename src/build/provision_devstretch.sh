#!/bin/bash
set -eu

# Sets up Debian (Stretch) to run OASIS with a useful "developer" configuration.
#
# Assumes oasis code is mounted at /opt/oasisqe/3.9  (Vagrant should do this)
# This is not appropriate for running a production site. It may be insecure.
#
# ToDo: allow this to run multiple times. ie. check things before doing them

date > /tmp/provision.notes
echo "Provisioning OASISDEV" >> /tmp/provision.notes

export SRC=/opt/oasisqe/src
export DEST=/opt/oasisqe/3.9

export LOGDIR=/var/log/oasisqe

mkdir -p ${DEST}/bin
cd ${DEST}

BINDIR=${DEST}/bin
OASISLIB=${DEST}

/bin/bash ${SRC}/src/build/install_systemdeps_stretch.sh
/bin/bash ${SRC}/src/build/setup_dev_pythonenv.sh

echo "Configuring for Development"

adduser --disabled-login --disabled-password --gecos OASIS oasisqe

DBPASS=`pwgen -s 16`

mkdir -p ${LOGDIR}
chown oasisqe ${LOGDIR}
touch ${LOGDIR}/main.log
chown oasisqe ${LOGDIR}/main.log

cp ${SRC}/docs/examples/sampleconfig.ini /etc/oasisqe.ini
sed -i "s/pass: SECRET/pass: ${DBPASS}/g" /etc/oasisqe.ini
sed -i "s/statichost: http:\/\/localhost/statichost: http:\/\/localhost:8083/g" /etc/oasisqe.ini
sed -i "s/url: http:\/\/localhost\/oasis/url: http:\/\/localhost:8083\/oasis/g" /etc/oasisqe.ini

su postgres -c "psql postgres <<EOF
  create user oasisqe;
  alter user oasisqe with password '${DBPASS}';
EOF"

su postgres  -c "createdb -O oasisqe oasisqe"
su oasisqe -c "${BINDIR}/oasisdb init"

cp ${SRC}/docs/examples/apache24config.sample /etc/apache2/sites-available/oasisqe.conf
export PYTHON_PATH=${DEST}
a2ensite oasisqe

service apache2 reload

export PS1=${PS1:-}
source ${DEST}/.venv/bin/activate
su oasisqe -c "${BINDIR}/create_test_topic EXAMPLE101 Samples"
echo
echo
echo OASISQE deployed to http://localhost:8083/oasis
echo
echo "********************************************"
su oasisqe -c "${BINDIR}/reset_admin_password devtest"
echo "********************************************"
