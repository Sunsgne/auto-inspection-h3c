#!/bin/bash
Linux_new_id=`ps -ef | grep manage.py | grep -v "grep" | awk '{print $2}'`
 
for id in $Linux_new_id
do
    kill -9 $id   
done
echo django service stopped
