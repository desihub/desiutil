#!/bin/bash
#
# Licensed under a 3-clause BSD style license - see LICENSE.rst
#
function usage() {
    local execName=$(basename $0)
    (
    echo "${execName} [-a VERSION] [-c CONFIG] [-h] [-m MODULESHOME] [-p PYTHON] [-t] [-v]"
    echo ""
    echo "Install desiutil on a bare system."
    echo ""
    ecoh "    -a = Version of DESI+Anaconda software stack."
    echo "    -c = Pass CONFIG to desiInstall."
    echo "    -h = Print this message and exit."
    echo "    -m = Look for the Modules install in MODULESHOME."
    echo "    -p = Use the Python executable PYTHON (e.g. /opt/local/bin/python2.7)."
    echo "    -t = Test mode.  Do not make any changes.  Implies -v."
    echo "    -v = Verbose mode. Print lots of extra information."
    ) >&2
}
#
# Get options
#
anaconda='current'
test=''
verbose=''
modules=''
py=''
config=''
while getopts c:hm:p:tv argname; do
    case ${argname} in
        a) anaconda=${OPTARG} ;;
        c) config="-c ${OPTARG}" ;;
        h) usage; exit 0 ;;
        m) modules=${OPTARG} ;;
        p) py=${OPTARG} ;;
        t) test='-t' ;;
        v) verbose='-v' ;;
        *) usage; exit 1 ;;
    esac
done
shift $((OPTIND-1))
#
# Install
#
if [[ -z "${DESI_PRODUCT_ROOT}" && -z "${NERSC_HOST}" ]]; then
    echo "You haven't set the DESI_PRODUCT_ROOT environment variable."
    echo "I'm not going to try to guess where you want to install things."
    exit 1
fi
if [[ -n "${modules}" ]]; then
    export MODULESHOME=${modules}
fi
if [[ -z "${MODULESHOME}" ]]; then
    echo "You do not appear to have Modules installed."
    exit 1
fi
#
# Export
#
git clone https://github.com/desihub/desiutil.git desiutil-master
export DESIUTIL=$(pwd)/desiutil-master
export PATH=${DESIUTIL}/bin:${PATH}
if [[ -z "${PYTHONPATH}" ]]; then
    export PYTHONPATH=${DESIUTIL}/py
else
    export PYTHONPATH=${DESIUTIL}/py:${PYTHONPATH}
fi
if [[ -z "${py}" ]]; then
    desiInstall -a ${anaconda} -b ${config} ${test} ${verbose}
else
    ${py} ${DESIUTIL}/bin/desiInstall -a ${anaconda} -b ${config} ${test} ${verbose}
fi
/bin/rm -rf ${DESIUTIL}
