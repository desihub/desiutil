#!/bin/bash
user=$1
uid=$(id -u ${user})
date=$2
group=desi
gid=58102
for f in 2 a; do
    grep -E "${uid}\|${desi}" ${date}.tlproject${f}.${group}.txt | \
        cut -d\| -f16 | \
        sed 's$%2F$/$g' | \
        sed "s%.snapshots/${date}/%%g"
done
