#!/bin/sh
cd /home/username/bots/
git checkout master
git tag -d temp_script_tag
git tag temp_script_tag
git pull

ERR=$?
if [ $ERR -ne 0 ]
    then git reset temp_script_tag --hard
fi

git tag -d temp_script_tag
/home/username/bots/example_bot.py &