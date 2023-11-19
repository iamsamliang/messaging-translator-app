#!/bin/sh -e
set -x

while read requirement; do
    poetry add "$requirement"
done < ../requirements.txt
