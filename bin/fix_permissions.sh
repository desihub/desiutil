#!/bin/sh
#
# Licensed under a 3-clause BSD style license - see LICENSE.rst
#
# See https://desi.lbl.gov/trac/wiki/Computing/NerscFileSystem#FileSystemAccess
# for the detailed requirements that motivate this script.
#
function usage() {
    local execName=$(basename $0)
    (
    echo "${execName} [-a] [-g GROUP] [-h] [-t] [-v] DIR"
    echo ""
    echo "Set group-friendly permissions on a directory tree."
    echo ""
    echo "    -a = Include apache/www access (via ACL) when modifying permissions."
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
apacheACL=''
apacheUID=48
desiGID=desi
test=False
verbose=False
while getopts ag:htv argname; do
    case ${argname} in
        a) apacheACL="u:${apacheUID}:rX" ;;
        g) desiGID=${OPTARG} ;;
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
# desiACL="u:${desiGID}:rwX"
if [ ! -x "${setfacl}" ]; then
    echo "Could not find the 'setfacl' command (tried ${setfacl})!" >&2
    echo "Skipping all ACL changes." >&2
    # desiACL=''
    apacheACL=''
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
    echo "Unable to determine NERSC environment.  Are you running this script at NERSC?" >&2
    exit 1
fi
#
# Proceed with permission changes.
#
findbase="${find} ${directory} -user ${USER}"
[ "${verbose}" = "True" ] && echo "Fixing permissions on ${directory} ..."
if [ "${test}" = "True" ]; then
    run ${verbose} "${findbase} -not -group ${desiGID} -not -type l -perm /g+w -ls"
    run ${verbose} "${findbase} -not -group ${desiGID} -not -type l -perm /o+rwx -ls"
    run ${verbose} "${findbase} -group ${desiGID} -not -type l -perm /o+w -ls"
    run ${verbose} "${findbase} -not -group ${desiGID} -ls"
    run ${verbose} "${findbase} -type f -not -perm /g+r -ls"
    run ${verbose} "${findbase} -type d -not -perm -g+rxs -ls"
    # if [ -n "${desiACL}" ]; then
    #     run ${verbose} "${findbase} -exec ${setfacl} --test --modify ${desiACL} {} ;"
    # fi
    if [ -n "${apacheACL}" ]; then
        run ${verbose} "${findbase} -exec ${setfacl} --test --modify ${apacheACL} {} ;"
    fi
else
    vflag=''
    #
    # Instruct chgrp & chmod to only report files that change.
    #
    [ "${verbose}" = "True" ] && vflag='-c'
    # Remove group write access from things not in the group.
    run ${verbose} "${findbase} -not -group ${desiGID} -not -type l -perm /g+w -exec chmod ${vflag} o-w {} ;"
    # Remove all world access from things not in the group.
    run ${verbose} "${findbase} -not -group ${desiGID} -not -type l -perm /o+rwx -exec chmod ${vflag} o-rwx {} ;"
    # Remove world write access from things already in the group.
    run ${verbose} "${findbase} -group ${desiGID} -not -type l -perm /o+w -exec chmod ${vflag} o-w {} ;"
    # Change group.
    run ${verbose} "${findbase} -not -group ${desiGID} -exec chgrp ${vflag} -h ${desiGID} {} ;"
    # Set group read access.
    run ${verbose} "${findbase} -type f -not -perm /g+r -exec chmod ${vflag} g+r {} ;"
    run ${verbose} "${findbase} -type d -not -perm -g+rxs -exec chmod ${vflag} g+rxs {} ;"
    # if [ -n "${desiACL}" ]; then
    #     run ${verbose} "${findbase} -exec ${setfacl} --modify ${desiACL} {} ;"
    # fi
    if [ -n "${apacheACL}" ]; then
        run ${verbose} "${findbase} -exec ${setfacl} --modify ${apacheACL} {} ;"
    fi
fi
