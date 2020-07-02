#!/bin/bash

type virtualenv >/dev/null 2>&1 ||echo  ` pip install virtualenv `
rm -rf env
virtualenv env 
source env/bin/activate
pip install -r requirements.txt
mv env/lib/python2.7/site-packages/crypto env/lib/python2.7/site-packages/Crypto
