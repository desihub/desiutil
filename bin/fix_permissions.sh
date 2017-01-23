#!/bin/sh
#
# Licensed under a 3-clause BSD style license - see LICENSE.rst
#
function usage() {
    local execName=$(basename $0)
    (
    echo "${execName} [-a] [-A] [-g GROUP] [-h] [-o] [-t] [-v] DIR"
    echo ""
    echo "Set group-friendly permissions on a directory tree."
    echo ""
    echo "    -a = Include apache/www access when modifying permissons."
    echo "    -A = Do NOT try to modify access control lists (ACL)."
    echo "    -g = Change group ownership to GROUP (default 'desi')."
    echo "    -h = Print this message and exit."
    echo "    -o = Set permissions for 'official' data; remove group-writeability."
    echo "    -t = Test mode.  Do not make any changes.  Implies -v."
    echo "    -v = Verbose mode. Print lots of extra information."
    echo "   DIR = Directory to fix. Required."
    ) >&2
}
#
#
#
function run() {
    local vrb=$1
    local cmd=$2
    [ "${vrb}" = "True" ] && echo "${cmd}"
    ${cmd}
}
#
# Get options
#
apache=''
apache_uid=48
acl=True
group=desi
official=False
default_acl='u::rwx,g::rwx,o::---'
default_chmod='g+w,o-rwx'
default_dir_chmod='2770'
gw='-not'
test=False
verbose=False
while getopts aAg:hotv argname; do
    case ${argname} in
        a) apache="u:${apache_uid}:rX" ;;
        A) acl=False ;;
        g) group=${OPTARG} ;;
        h) usage; exit 0 ;;
        o) official=True; default_acl='u::rwx,g::r-x,o::---'; default_chmod='g-w,o-rwx'; default_dir_chmod='2750'; gw='' ;;
        t) test=True; verbose=True ;;
        v) verbose=True ;;
        *) usage; exit 1 ;;
    esac
done
shift $((OPTIND-1))
#
# Check for commands
#
find=/usr/bin/find
if [ ! -x "${find}" ]; then
    echo "Could not find the 'find' command (tried ${find})!" >&2
    exit 1
fi
setfacl=/usr/bin/setfacl
if [ ! -x "${setfacl}" ]; then
    echo "Could not find the 'setfacl' command (tried ${setfacl})!" >&2
    echo "Skipping ACL changes." >&2
    acl=False
fi
#
# Make sure directory exists, and check consistency.
#
if [ $# -lt 1 ]; then
    echo "You must specify a directory!" >&2
    usage
    exit 1
fi
directory=$1
if [ ! -d "${directory}" ]; then
    echo "${directory} does not exist or is not a directory!" >&2
    usage
    exit 1
fi
if [ -z "${USER}" ]; then
    echo "The USER environment variable does not appear to be set!" >&2
    exit 1
fi
if [ -z "${NERSC_HOST}" ]; then
    echo "Unable to determine NERSC environment.  Are you running this script at NERSC?"
    exit 1
fi
if [ -n "${apache}" -a "${acl}" = "False" ]; then
    echo "You are attempting to set apache permissions, while simultaneously disabling ACL altogether. Pick one or the other."
    exit 1
fi
#
# Proceed with permission changes.
#
[ "${verbose}" = "True" ] && echo "Fixing permissions on ${directory} ..."
if [ "${test}" = "True" ]; then
    run ${verbose} "${find} ${directory} -user ${USER} -not -group ${group} -ls"
    run ${verbose} "${find} ${directory} -user ${USER} -type f -not -perm /g+r -ls"
    run ${verbose} "${find} ${directory} -user ${USER} -type f ( -perm /o+rwx -or ${gw} -perm /g+w ) -ls"
    run ${verbose} "${find} ${directory} -user ${USER} -type d -not -perm ${default_dir_chmod} -ls"
    if [ "${acl}" = "True" ]; then
        run ${verbose} "${find} ${directory} -user ${USER} -exec ${setfacl} --test --remove-all {} ;"
        run ${verbose} "${find} ${directory} -user ${USER} -type d -exec ${setfacl} --test --default -m ${default_acl} {} ;"
        if [ -n "${apache}" ]; then
            run ${verbose} "${find} ${directory} -user ${USER} -exec ${setfacl} --test -m ${apache} {} ;"
            run ${verbose} "${find} ${directory} -user ${USER} -type d -exec ${setfacl} --test --default -m ${apache} {} ;"
        fi
    fi
else
    vflag=''
    #
    # Instruct chgrp & chmod to only report files that change.
    #
    [ "${verbose}" = "True" ] && vflag='-c'
    run ${verbose} "${find} ${directory} -user ${USER} -not -group ${group} -exec chgrp ${vflag} -h ${group} {} ;"
    run ${verbose} "${find} ${directory} -user ${USER} -type f -not -perm /g+r -exec chmod ${vflag} g+r {} ;"
    run ${verbose} "${find} ${directory} -user ${USER} -type f ( -perm /o+rwx -or ${gw} -perm /g+w ) -exec chmod ${vflag} ${default_chmod} {} ;"
    run ${verbose} "${find} ${directory} -user ${USER} -type d -not -perm ${default_dir_chmod} -exec chmod ${vflag} ${default_dir_chmod} {} ;"
    if [ "${acl}" = "True" ]; then
        run ${verbose} "${find} ${directory} -user ${USER} -exec ${setfacl} --remove-all {} ;"
        run ${verbose} "${find} ${directory} -user ${USER} -type d -exec ${setfacl} --default -m ${default_acl} {} ;"
        if [ -n "${apache}" ]; then
            run ${verbose} "${find} ${directory} -user ${USER} -exec ${setfacl} -m ${apache} {} ;"
            run ${verbose} "${find} ${directory} -user ${USER} -type d -exec ${setfacl} --default -m ${apache} {} ;"
        fi
    fi
fi
