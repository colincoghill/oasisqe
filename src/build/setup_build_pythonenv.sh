#!/bin/bash

# Intended to be called by provision_ scripts.
#
# Assumes OASIS src is installed in ${SRC}
# Will install a pipenv into ${DEST} and copy OASIS files into it
# The intent is that they can then be packaged up for distribution
# or testing.

date > /tmp/provision.notes
echo "Installing OASIS to pipenv" >> /tmp/provision.notes

BINDIR=${DEST}/bin
OASISLIB=${DEST}

export PIPENV_VENV_IN_PROJECT=1

sudo cp -R ${SRC}/src/oasis ${DEST}
sudo cp -R ${SRC}/src/scripts ${DEST}
sudo cp -R ${SRC}/src/fonts ${DEST}
sudo cp -R ${SRC}/src/static ${DEST}
sudo cp -R ${SRC}/src/templates ${DEST}
sudo cp -R ${SRC}/src/sql ${DEST}
sudo cp -R ${SRC}/src/oasis.wsgi ${DEST}

sudo cp ${SRC}/src/Pipfile ${DEST}
sudo cp ${SRC}/src/Pipfile.lock ${DEST}

sudo chown -R vagrant ${DEST}

cd ${DEST}

PIP_IGNORE_INSTALLED=1 pipenv install

sudo mkdir ${BINDIR}

echo "OASISLIB=${OASISLIB}" >> ${DEST}/.env

# binaries need a wrapper to find our pipenv
cat << EOF > ${BINDIR}/oasisdb
#!/bin/bash
export OASISLIB=${DEST}
source ${DEST}/.venv/bin/activate
python ${DEST}/scripts/oasisdb \$@
EOF
chmod +x ${BINDIR}/oasisdb

cat << EOF > ${BINDIR}/create_test_topic
#!/bin/bash
export OASISLIB=${DEST}
source ${DEST}/.venv/bin/activate
python ${DEST}/scripts/create_test_topic \$@
EOF
chmod +x ${BINDIR}/create_test_topic

cat << EOF > ${BINDIR}/reset_admin_password
#!/bin/bash
export OASISLIB=${DEST}
source ${DEST}/.venv/bin/activate
python ${DEST}/scripts/reset_admin_password \$@
EOF
chmod +x ${BINDIR}/reset_admin_password

echo "Built into pipenv ${DEST}"

