# PiTFT-lakechamplain-temp
Gets the temperature of the lake in Lake Champlain and displays it to a raspberry pi screen.

# Required Libraries:

pygame

matplotlib

datetime

climata

requests

bs4

pillow

pandas (If you have problems, install it separately with "pip3 install python3-pandas")

# Startup:
Run:
```
cd /Documents/Github/PiTFT-lakechamplain-temp/

MPLBACKEND=Agg python3 ./pygameElements/__init__.py
```

# SDL fix:
Run:
```
sudo fixsdl.sh
```