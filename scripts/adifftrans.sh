#!/bin/bash -x

# show difference between this transaction and the previous transaction

if [[ $# -ne 2 ]]; then
    echo "usage: $0 <stream> <transaction>"
    exit 1
fi

STREAM=$1
TRANS=$2

accurev diff  -a -i -v $STREAM -V $STREAM -t $((TRANS-1))-$TRANS | grep "changed from"| while read element changed from v1 to v2; do
    accurev diff $element -v $v2 -V $v1 -- "-u"
done
