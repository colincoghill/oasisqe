#!/bin/bash
set -eu

# Intended to be called by provision_ scripts.
#
# Assumes OASIS src is installed in ${SRC}
# Will install a pipenv into ${DEST} and symlink OASIS files into it
# suitable for development as the files can be edited on the host
# and changes will apear "live". (may need to reload apache2 to get them)

date > /tmp/provision.notes
echo "Linking OASIS to pipenv" >> /tmp/provision.notes

BINDIR=${DEST}/bin
OASISLIB=${DEST}

mkdir -p ${DEST}/bin
cd ${DEST}

export PIPENV_VENV_IN_PROJECT=1

sudo ln -sf ${SRC}/src/oasis ${DEST}
sudo ln -sf ${SRC}/src/scripts ${DEST}
sudo ln -sf ${SRC}/src/fonts ${DEST}
sudo ln -sf ${SRC}/src/static ${DEST}
sudo ln -sf ${SRC}/src/templates ${DEST}
sudo ln -sf ${SRC}/src/sql ${DEST}
sudo ln -sf ${SRC}/src/oasis.wsgi ${DEST}

sudo ln -sf ${SRC}/src/Pipfile ${DEST}
sudo ln -sf ${SRC}/src/Pipfile.lock ${DEST}

sudo chown -R vagrant ${DEST}

cd ${DEST}

PIP_IGNORE_INSTALLED=1 pipenv --python 3.6 install --dev

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

echo "Linked into pipenv ${DEST}"

