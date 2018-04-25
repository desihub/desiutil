#!/bin/bash
#
# Licensed under a 3-clause BSD style license - see LICENSE.rst
#
# This script is for testing fix_permissions.sh.  It should only be run at NERSC.
#
function usage() {
    local execName=$(basename $0)
    (
    echo "${execName} [-h] [-v]"
    echo ""
    echo "Test the fix_permissions.sh script."
    echo ""
    echo "    -h = Print this message and exit."
    echo "    -v = Verbose mode. Print lots of extra information."
    ) >&2
}
#
# Get options
#
verbose=''
while getopts hv argname; do
    case ${argname} in
        h) usage; exit 0 ;;
        v) verbose='-v' ;;
        *) usage; exit 1 ;;
    esac
done
shift $((OPTIND-1))
#
# Set up test cases.
#
dirPerm=(0777 0775 0750 0700)
filePerm=(0666 0664 0640 0600)
fixedDirPerm=(group::rwx group::rwx group::r-x group::r-x)
fixedFilePerm=(group::rw- group::rw- group::r-- group::r--)
#
# Run tests.
#
for k in $(seq 0 3); do
    [[ -n "${verbose}" ]] && echo /bin/rm -rf Dir${k}
    /bin/rm -rf Dir${k}
    [[ -n "${verbose}" ]] && echo mkdir Dir${k}
    mkdir Dir${k}
    [[ -n "${verbose}" ]] && echo chmod ${dirPerm[$k]} Dir${k}
    chmod ${dirPerm[$k]} Dir${k}
    [[ -n "${verbose}" ]] && echo touch Dir${k}/File${k}
    touch Dir${k}/File${k}
    [[ -n "${verbose}" ]] && echo chmod ${filePerm[$k]} Dir${k}/File${k}
    chmod ${filePerm[$k]} Dir${k}/File${k}
    [[ -n "${verbose}" ]] && echo fix_permissions.sh ${verbose} Dir${k}
    fix_permissions.sh ${verbose} Dir${k}
    [[ $(getfacl -c Dir${k} | grep group) == ${fixedDirPerm[$k]} ]] || echo "Dir${k}/ permission not set properly!"
    [[ $(stat -c %G Dir${k}) == desi ]] || echo "Dir${k}/ group ID not set properly!"
    [[ $(getfacl -c Dir${k} | grep desi) == user:desi:rwx ]] || echo "Dir${k}/ ACL not set properly!"
    [[ $(getfacl -c Dir${k}/File${k} | grep group) == ${fixedFilePerm[$k]} ]] || echo "Dir${k}/File${k} permission not set properly!"
    [[ $(stat -c %G Dir${k}/File${k}) == desi ]] || echo "Dir${k}/File${k} group ID not set properly!"
    [[ $(getfacl -c Dir${k}/File${k} | grep desi) == user:desi:rw- ]] || echo "Dir${k}/File${k} ACL not set properly!"
done
