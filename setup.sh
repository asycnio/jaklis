#!/bin/bash

for i in gcc python3-pip python3-setuptools libpq-dev python3-dev; do
	if [ $(dpkg-query -W -f='${Status}' $i 2>/dev/null | grep -c "ok installed") -eq 0 ];
	then
		sudo apt install -y $i
	fi
done

pip3 install -r requirements.txt
chmod u+x dialog.py
