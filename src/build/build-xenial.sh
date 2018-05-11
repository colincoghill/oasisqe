#!/bin/sh -e

# Usage:
#    build.sh SRCDIR DSTDIR

# builds OASIS into current dir. uses a python virtualenv (pipenv) and pulls in dependencies
# the intent is you'd run this under a clean (vagrant?) install of target OS to get the
# right dependencies set up. you can then tar up the build and it should, in theory, work
# on a clean install of that OS

SRC=$1
DEST=$2

sudo pip install pipenv
export PIPENV_VENV_IN_PROJECT=1

sudo mkdir -p ${DEST}

sudo cp -R ${SRC}/src/oasis ${DEST}
sudo cp -R ${SRC}/src/scripts ${DEST}
sudo cp -R ${SRC}/src/fonts ${DEST}
sudo cp -R ${SRC}/src/static ${DEST}
sudo cp -R ${SRC}/src/templates ${DEST}
sudo cp -R ${SRC}/src/sql ${DEST}
sudo mkdir ${DEST}/bin

sudo cp ${SRC}/src/Pipfile ${DEST}
sudo cp ${SRC}/src/Pipfile.lock ${DEST}

sudo chown -R vagrant ${DEST}

cd ${DEST}

PIP_IGNORE_INSTALLED=1 pipenv install 

cat << EOF > bin/oasisdb
#!/bin/bash
export OASISLIB=${DEST}
source ${DEST}/.venv/bin/activate
${DEST}/scripts/oasisdb \$@
EOF

chmod +x bin/oasisdb

echo "Built into ${DEST}"

