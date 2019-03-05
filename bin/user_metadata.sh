#!/bin/bash
user=$1
uid=$(id -u ${user})
date=$2
group=desi
gid=58102
root=/global/project/projectdirs/${group}/metadata
for f in 2 a; do
    grep -E "${uid}\|${desi}" ${root}/${date}.tlproject${f}.${group}.txt | \
        cut -d\| -f16 | \
        sed 's$%2F$/$g' | \
        sed "s%.snapshots/${date}/%%g"
done
