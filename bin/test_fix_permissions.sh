#!/bin/bash
#
# Licensed under a 3-clause BSD style license - see LICENSE.rst
#
# This script is for testing fix_permissions.sh.  It should only be run at NERSC.
#
dirPerm=(0777 0775 0750 0700)
filePerm=(0666 0664 0640 0600)
fixedDirPerm=(2770 2770 2750 2750)
fixedFilePerm=(660 660 640 640)
for k in $(seq 0 3); do
    echo /bin/rm -rf Dir${k}
    /bin/rm -rf Dir${k}
    echo mkdir Dir${k}
    mkdir Dir${k}
    echo chmod ${dirPerm[$k]} Dir${k}
    chmod ${dirPerm[$k]} Dir${k}
    echo touch Dir${k}/File${k}
    touch Dir${k}/File${k}
    echo chmod ${filePerm[$k]} Dir${k}/File${k}
    chmod ${filePerm[$k]} Dir${k}/File${k}
    echo fix_permissions.sh -v Dir${k}
    fix_permissions.sh -v Dir${k}
    [[ $(stat -c %a Dir${k}) == ${fixedDirPerm[$k]} ]] || echo "Dir${k}/ permission not set properly!"
    [[ $(stat -c %G Dir${k}) == desi ]] || echo "Dir${k}/ group ID not set properly!"
    [[ $(getfacl -c Dir${k} | grep desi) == user:desi:rwx ]] || echo "Dir${k}/ ACL not set properly!"
    [[ $(stat -c %a Dir${k}/File${k}) == ${fixedFilePerm[$k]} ]] || echo "Dir${k}/File${k} permission not set properly!"
    [[ $(stat -c %G Dir${k}/File${k}) == desi ]] || echo "Dir${k}/File${k} group ID not set properly!"
    [[ $(getfacl -c Dir${k}/File${k} | grep desi) == user:desi:rw- ]] || echo "Dir${k}/File${k} ACL not set properly!"
done
