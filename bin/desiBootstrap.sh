#!/bin/bash
#
# Licensed under a 3-clause BSD style license - see LICENSE.rst
#
function usage() {
    local execName=$(basename $0)
    (
    echo "${execName} [-a VERSION] [-b BRANCH] [-c CONFIG] [-h] [-m MODULESHOME] [-p PYTHON] [-t] [-v]"
    echo ""
    echo "Install desiutil on a bare system."
    echo ""
    echo "    -a = Version of DESI+Anaconda software stack."
    echo "    -b = Switch to desiutil BRANCH before installing."
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
branch=''
modules=''
config=''
py=''
test=''
verbose=''
while getopts a:b:c:hm:p:tv argname; do
    case ${argname} in
        a) anaconda=${OPTARG} ;;
        b) branch=${OPTARG} ;;
        c) config="-c ${OPTARG}" ;;
        h) usage; exit 0 ;;
        m) modules=${OPTARG} ;;
        p) py=${OPTARG} ;;
        t) test='-t'; verbose='-v' ;;
        v) verbose='-v' ;;
        *) usage; exit 1 ;;
    esac
done
shift $((OPTIND-1))
#
# Validate options
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
if [[ -n "${NERSC_HOST}" && -z "${py}" ]]; then
    #
    # Make certain we are using the Python version associated with the
    # specified DESI+Anaconda stack.
    #
    common_root=/global/common/${NERSC_HOST}/contrib/desi/desiconda/${anaconda}
    software_root=/global/project/projectdirs/desi/software/${NERSC_HOST}/desiconda/${anaconda}
    for d in ${common_root} ${software_root}; do
        if [[ -d ${d} ]]; then
            if [[ "${anaconda}" == "current" ]]; then
                anaconda=$(readlink ${d})
                dd=$(dirname ${d})/${anaconda}
            else
                dd=${d}
            fi
            py=${dd}/code/desiconda/${anaconda}_conda/bin/python
            if [[ ! -x ${py} ]]; then
                echo "Python executable not found!"
                exit 1
            fi
        fi
    done
    if [[ -z "${py}" ]]; then
        echo "Could not find Python executable associated with '${anaconda}' on ${NERSC_HOST}!"
        exit 1
    fi
fi
#
# Export
#
[[ -n "${verbose}" ]] && echo git clone https://github.com/desihub/desiutil.git desiutil-master
git clone https://github.com/desihub/desiutil.git desiutil-master
if [[ -n "${branch}" ]]; then
    cd desiutil-master
    [[ -n "${verbose}" ]] && echo git checkout ${branch}
    git checkout ${branch}
    cd ..
fi
export DESIUTIL=$(pwd)/desiutil-master
export PATH=${DESIUTIL}/bin:${PATH}
if [[ -z "${PYTHONPATH}" ]]; then
    export PYTHONPATH=${DESIUTIL}/py
else
    export PYTHONPATH=${DESIUTIL}/py:${PYTHONPATH}
fi
if [[ -z "${py}" ]]; then
    [[ -n "${verbose}" ]] && echo desiInstall -a ${anaconda} -b ${config} ${test} ${verbose}
    desiInstall -a ${anaconda} -b ${config} ${test} ${verbose}
else
    [[ -n "${verbose}" ]] && echo ${py} ${DESIUTIL}/bin/desiInstall -a ${anaconda} -b ${config} ${test} ${verbose}
    ${py} ${DESIUTIL}/bin/desiInstall -a ${anaconda} -b ${config} ${test} ${verbose}
fi
[[ -n "${verbose}" ]] && echo /bin/rm -rf ${DESIUTIL}
/bin/rm -rf ${DESIUTIL}
