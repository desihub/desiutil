#!/bin/bash
#
# Licensed under a 3-clause BSD style license - see LICENSE.rst
#
function usage() {
    local execName=$(basename $0)
    (
    echo "${execName} [-g GROUP] [-h] USER YYYY-MM-DD"
    echo ""
    echo "Extract a user's files from the metadata snapshots."
    echo ""
    echo "        -g = Use GROUP instead of desi."
    echo "        -h = Print this message and exit."
    echo "      USER = NERSC user name."
    echo "YYYY-MM-DD = Snapshot date."
    ) >&2
}
#
# Options.
#
group=desi
while getopts g:h argname; do
    case ${argname} in
        g) group=${OPTARG} ;;
        h) usage; exit 0 ;;
        *) usage; exit 1 ;;
    esac
done
shift $((OPTIND-1))
if [[ $# < 2 ]]; then
    echo "Missing required arguments!" >&2
    usage
    exit 1
fi
user=$1
date=$2
uid=$(id -u ${user})
gid=$(id -g ${group})
root=/global/cfs/cdirs/${group}/metadata
for filesystem in cfs tlprojecta; do
    grep -E "${uid}\|${group}" ${root}/${date}.${filesystem}.${group}.txt | \
        cut -d\| -f16 | \
        sed 's$%2F$/$g' | \
        sed "s%.snapshots/${date}/%%g"
done
