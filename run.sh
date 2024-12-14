#! /bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# Check if python3 python3-flask are installed
if [ -z "$(which python3)" ] || [ -z "$(which flask)" ]
  then echo "Please re-run install.sh"
  exit
fi

# Clean up
sudo bash clean.sh

cd scripts
sudo python3 server.py
cd ..
