# PiTFT-champlain-scheduler
A pycharm information and utility app for common room computers.

Supports a variety of pages containing information useful to students attending Champlain College:
- Mainstreet Landing Movies
- Graph of Lake Temperature
- Live Burlington Pictures Feed

Planned Pages:
- User Profiles/Preferences
  - Enables/Disables pages
- Shuttle Tracking in relation to class times
  - Requires Profile Sign-in with google calendar
- Display of Shuttle Locations
- Washer/Drier status
- Weather and temperature


Initially built for raspberry pi.
Lake temperature

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