#!/bin/bash

cd ~
export PYTHONPATH=.local/lib/python3.7:$PYTHONPATH

# sudo chmod -R ugo+rX /home/pi/.local/lib/python3.7/site-packages/

cd "/home/pi/Documents/Github/PiTFT-lakechamplain-temp/"

git pull

MPLBACKEND=Agg python3 ./pygameElements/__init__.py
