#!/bin/sh
#
# $Id$
#
function usage() {
    local execName=$(basename $0)
    (
    echo "${execName} [-g GROUP] [-h] [-t] [-v] DIR"
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
    local tst=$1
    local vrb=$2
    local cmd=$3
    [ "${vrb}" = "True" ] && echo "${cmd}"
    [ "${tst}" = "True" ] || ${cmd}
}
#
# Get options
#
test=False
verbose=False
group=desi
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
# Check for find
#
find=/usr/bin/find
if [ ! -x "${find}" ]; then
    echo "Could not find the 'find' command (tried ${find})!" >&2
    exit 1
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
run ${test} ${verbose} "${find} ${directory} -user ${USER} -not -group ${group} -exec chgrp -h ${group} {} ;"
run ${test} ${verbose} "${find} ${directory} -user ${USER} -type f -not -perm 660 -exec chmod -v 660 {} ;"
run ${test} ${verbose} "${find} ${directory} -user ${USER} -type d -not -perm 2770 -exec chmod -v 2770 {} ;"
