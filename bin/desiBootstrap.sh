#!/bin/bash
#
# $Id$
#
function usage() {
    local execName=$(basename $0)
    (
    echo "${execName} [-U USER] [-h] [-t] [-v]"
    echo ""
    echo "Install desiUtil on a bare system."
    echo ""
    echo "    -U = Set the svn username to USER (default '${USER}')."
    echo "    -h = Print this message and exit."
    echo "    -t = Test mode.  Do not make any changes.  Implies -v."
    echo "    -v = Verbose mode. Print lots of extra information."
    ) >&2
}
#
# Get options
#
test=''
verbose=''
u=${USER}
while getopts U:htv argname; do
    case ${argname} in
        U) u=${OPTARG} ;;
        h) usage; exit 0 ;;
        t) test='-t' ;;
        v) verbose='-v' ;;
        *) usage; exit 1 ;;
    esac
done
shift $((OPTIND-1))
#
# Install
#
if test -z "${DESI_PRODUCT_ROOT}" -a -z "${NERSC_HOST}"; then
    echo "You haven't set the DESI_PRODUCT_ROOT environment variable."
    echo "I'm not going to try to guess where you want to install things."
    exit 1
fi
svn --username ${u} export https://desi.lbl.gov/svn/code/tools/desiUtil/trunk desiUtil-trunk
export DESIUTIL_DIR=$(pwd)/desiUtil-trunk
export PATH=${DESIUTIL_DIR}/bin:${PATH}
if test -z "${PYTHONPATH}"; then
    export PYTHONPATH=${DESIUTIL_DIR}/py
else
    export PYTHONPATH=${DESIUTIL_DIR}/py:${PYTHONPATH}
fi
desiInstall -b -U ${u} ${test} ${verbose}
/bin/rm -rf desiUtil-trunk
