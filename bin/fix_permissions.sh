#!/bin/sh
#
# $Id$
#
function usage() {
    local execName=$(basename $0)
    (
    echo "${execName} [-g GROUP] [-h] [-t] [-v] DIR"
    echo ""
    echo "Set group-friendly permissions on a directory tree."
    echo ""
    echo "    -g = Change group ownership to GROUP (default 'desi')."
    echo "    -h = Print this message and exit."
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
test=False
verbose=False
group=desi
acl=True
while getopts g:htv argname; do
    case ${argname} in
        g) group=${OPTARG} ;;
        h) usage; exit 0 ;;
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
# Make sure directory exists
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
[ "${verbose}" = "True" ] && echo "Fixing permissions on ${directory} ..."
if [ "${test}" = "True" ]; then
    run ${verbose} "${find} ${directory} -user ${USER} -not -group ${group} -ls"
    run ${verbose} "${find} ${directory} -user ${USER} -type f -not -perm 660 -ls"
    run ${verbose} "${find} ${directory} -user ${USER} -type d -not -perm 2770 -ls"
    if [ "${acl}" = "True" ]; then
        run ${verbose} "${find} ${directory} -user ${USER} -type f -exec ${setfacl} --test --remove-all {} ;"
        run ${verbose} "${find} ${directory} -user ${USER} -type d -exec ${setfacl} --test --remove-all {} ;"
        run ${verbose} "${setfacl} --test --recursive --default -m u::rwx,g::rwx,o::--- ${directory}"
    fi
else
    vflag=''
    [ "${verbose}" = "True" ] && vflag='-v'
    run ${verbose} "${find} ${directory} -user ${USER} -not -group ${group} -exec chgrp ${vflag} -h ${group} {} ;"
    run ${verbose} "${find} ${directory} -user ${USER} -type f -not -perm 660 -exec chmod ${vflag} 660 {} ;"
    run ${verbose} "${find} ${directory} -user ${USER} -type d -not -perm 2770 -exec chmod ${vflag} 2770 {} ;"
    if [ "${acl}" = "True" ]; then
        run ${verbose} "${find} ${directory} -user ${USER} -type f -exec ${setfacl} --remove-all {} ;"
        run ${verbose} "${find} ${directory} -user ${USER} -type d -exec ${setfacl} --remove-all {} ;"
        run ${verbose} "${setfacl} --recursive --default -m u::rwx,g::rwx,o::--- ${directory}"
    fi
fi