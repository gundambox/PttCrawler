#!/bin/bash
cd $1
shift;

if [ -n $1 ]
then
    source $1/bin/activate
fi
shift;

python "$@"