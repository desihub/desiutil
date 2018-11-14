#!/bin/bash
#
# Licensed under a 3-clause BSD style license - see LICENSE.rst
#
# This script is for testing fix_permissions.sh.  It should only be run at NERSC.
#
function usage() {
    local execName=$(basename $0)
    (
    echo "${execName} [-g GROUP] [-h] [-v]"
    echo ""
    echo "Test the fix_permissions.sh script."
    echo ""
    echo "    -g = Override the starting group (default `id -ng`)."
    echo "    -h = Print this message and exit."
    echo "    -v = Verbose mode. Print lots of extra information."
    ) >&2
}
#
# Get options
#
verbose=''
GROUP=$(id -ng)
while getopts g:hv argname; do
    case ${argname} in
        g) GROUP=${OPTARG} ;;
        h) usage; exit 0 ;;
        v) verbose='-v' ;;
        *) usage; exit 1 ;;
    esac
done
shift $((OPTIND-1))
#
# Set up test cases.
#
g=(${GROUP} ${GROUP} ${GROUP} ${GROUP} desi desi desi desi ${GROUP} desi)
dirPerm=(0777 0775 0750 0700 0777 0775 0750 0700 0700 0700)
filePerm=(0666 0664 0640 0600 0666 0664 0640 0600 0600 0600)
fixedDirPerm=(2777 2775 2750 2750 2775 2775 2750 2750 2750 2750)
# fixedDirPerm=(group::rwx group::rwx group::r-x group::r-x)
# fixedFilePerm=(group::rw- group::rw- group::r-- group::r--)
fixedFilePerm=(666 664 640 640 664 664 640 640 640 640)
#
# Run tests.
#
for k in $(seq 0 9); do
    [[ -n "${verbose}" ]] && echo /bin/rm -rf Dir${k}
    /bin/rm -rf Dir${k}
    [[ -n "${verbose}" ]] && echo mkdir Dir${k}
    mkdir Dir${k}
    [[ -n "${verbose}" ]] && echo chgrp ${g[$k]} Dir${k}
    chgrp ${g[$k]} Dir${k}
    [[ -n "${verbose}" ]] && echo chmod ${dirPerm[$k]} Dir${k}
    chmod ${dirPerm[$k]} Dir${k}
    [[ -n "${verbose}" ]] && echo touch Dir${k}/File${k}
    touch Dir${k}/File${k}
    [[ -n "${verbose}" ]] && echo chgrp ${g[$k]} Dir${k}/File${k}
    chgrp ${g[$k]} Dir${k}/File${k}
    [[ -n "${verbose}" ]] && echo chmod ${filePerm[$k]} Dir${k}/File${k}
    chmod ${filePerm[$k]} Dir${k}/File${k}
    [[ -n "${verbose}" ]] && echo fix_permissions.sh ${verbose} Dir${k}
    if (( k >= 8 )); then
        fix_permissions.sh -a ${verbose} Dir${k}
    else
        fix_permissions.sh ${verbose} Dir${k}
    fi
    [[ $(stat -c %a Dir${k}) == ${fixedDirPerm[$k]} ]] || echo "Dir${k}/ permission not set properly!"
    [[ $(stat -c %G Dir${k}) == desi ]] || echo "Dir${k}/ group ID not set properly!"
    if (( k >= 8 )); then
        [[ $(getfacl -c Dir${k} | grep 48) == user:48:r-x ]] || echo "Dir${k}/ ACL not set properly!"
        [[ $(getfacl -c Dir${k}/File${k} | grep 48) == user:48:r-- ]] || echo "Dir${k}/File${k} ACL not set properly!"
    fi
    [[ $(stat -c %a Dir${k}/File${k}) == ${fixedFilePerm[$k]} ]] || echo "Dir${k}/File${k} permission not set properly!"
    [[ $(stat -c %G Dir${k}/File${k}) == desi ]] || echo "Dir${k}/File${k} group ID not set properly!"
done
