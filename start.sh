#!/bin/bash
currentpath=$(cd `dirname $0`; pwd)
python3 manage.py runserver 0.0.0.0:9992 > $currentpath/log/console.log 2>&1 &
echo django service is starting ...
echo started success!
