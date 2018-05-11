#!/bin/sh -e

# Usage:
#    build.sh SRCDIR DSTDIR

# builds OASIS into current dir. uses a python virtualenv (pipenv) and pulls in dependencies
# the intent is you'd run this under a clean (vagrant?) install of target OS to get the
# right dependencies set up. you can then tar up the build and it should, in theory, work
# on a clean install of that OS

SRC=$1
BDIR=$2

sudo pip install pipenv
export PIPENV_VENV_IN_PROJECT=1

mkdir -p ${BDIR}

cp -R ${SRC}/src/oasis ${BDIR}
cp -R ${SRC}/src/scripts ${BDIR}
cp -R ${SRC}/src/fonts ${BDIR}
cp -R ${SRC}/src/static ${BDIR}
cp -R ${SRC}/src/templates ${BDIR}
cp -R ${SRC}/src/sql ${BDIR}
mkdir ${BDIR}/bin

cp ${SRC}/src/Pipfile ${BDIR}
cp ${SRC}/src/Pipfile.lock ${BDIR}

cd ${BDIR}

PIP_IGNORE_INSTALLED=1 pipenv install 

cat << EOF > bin/oasisdb
#!/bin/bash
export OASISLIB=${BDIR}
source ${BDIR}/.venv/bin/activate
${BDIR}/scripts/oasisdb \$@
EOF

chmod +x bin/oasisdb

echo "Built into ${BDIR}"

