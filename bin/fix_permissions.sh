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
    ${vrb} && echo "${cmd}"
    ${cmd}
}
#
# Get options
#
apacheACL=''
apacheUID=48
desiGID=desi
test=/usr/bin/false
verbose=/usr/bin/false
while getopts ag:htv argname; do
    case ${argname} in
        a) apacheACL="u:${apacheUID}:rX" ;;
        g) desiGID=${OPTARG} ;;
        h) usage; exit 0 ;;
        t) test=/usr/bin/true; verbose=/usr/bin/true ;;
        v) verbose=/usr/bin/true ;;
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
    echo "Skipping all ACL changes." >&2
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
if [ $(realpath ${directory}) = $(realpath ${HOME}) ]; then
    echo "You are attempting to change the permissions of HOME=${HOME}, which is dangerous.  Aborting." >&2
    exit 1
fi
#
# Proceed with permission changes.
#
findbase="${find} ${directory} -user ${USER}"
${verbose} && echo "Fixing permissions on ${directory} ..."
if ${test}; then
    run ${verbose} "${findbase} -not -group ${desiGID} -ls"
    run ${verbose} "${findbase} -type f -not -perm /g+r -ls"
    run ${verbose} "${findbase} -type d -not -perm -g+rxs -ls"
    if [ -n "${apacheACL}" ]; then
        run ${verbose} "${findbase} -exec ${setfacl} --test --modify ${apacheACL} {} ;"
    fi
else
    vflag=''
    #
    # Instruct chgrp & chmod to only report files that change.
    #
    ${verbose} && vflag='-c'
    # Change group.
    run ${verbose} "${findbase} -not -group ${desiGID} -exec chgrp ${vflag} -h ${desiGID} {} ;"
    # Set group read access.
    run ${verbose} "${findbase} -type f -not -perm /g+r -exec chmod ${vflag} g+r {} ;"
    run ${verbose} "${findbase} -type d -not -perm -g+rxs -exec chmod ${vflag} g+rxs {} ;"
    if [ -n "${apacheACL}" ]; then
        run ${verbose} "${findbase} -exec ${setfacl} --modify ${apacheACL} {} ;"
    fi
fi
#
# Notes on searching for group-unreadable files.
#
# getfacl -R -t /global/cfs/cdirs//desi/spectro/ | grep -e '^# file:' -e '^GROUP' | sed -n 'h;n;G;p' | paste - - | awk '$3=="---" {print}'
#
# in a few minutes I didn't find any with "---" group ACL, but if I change to searching for things with a "r--" ACL, a sample of the output looks like:
# sleak@cori06$ getfacl -R -t /global/cfs/cdirs//desi/spectro/ | grep -e '^# file:' -e '^GROUP' | sed -n 'h;n;G;p' | paste - - | awk '$3=="r--" {print}' | head
# getfacl: Removing leading '/' from absolute path names
# GROUP desi r-- # file: global/cfs/cdirs//desi/spectro//ql_calib/fiberflat-z7.fits
# GROUP desi r-- # file: global/cfs/cdirs//desi/spectro//ql_calib/fiberflat-z3.fits
# GROUP desi r-- # file: global/cfs/cdirs//desi/spectro//ql_calib/fiberflat-b2.fits
# GROUP desi r-- # file: global/cfs/cdirs//desi/spectro//ql_calib/fiberflat-z4.fits
# GROUP desi r-- # file: global/cfs/cdirs//desi/spectro//ql_calib/fiberflat-b7.fits
# GROUP desi r-- # file: global/cfs/cdirs//desi/spectro//ql_calib/fiberflat-z6.fits
# GROUP desi r-- # file: global/cfs/cdirs//desi/spectro//ql_calib/fiberflat-b4.fits
# GROUP desi r-- # file: global/cfs/cdirs//desi/spectro//ql_calib/fiberflat-r7.fits
# GROUP desi r-- # file: global/cfs/cdirs//desi/spectro//ql_calib/fiberflat-b9.fits
# GROUP desi r-- # file: global/cfs/cdirs//desi/spectro//ql_calib/fiberflat-r0.fits
