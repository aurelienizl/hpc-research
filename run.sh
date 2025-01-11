#! /bin/bash

set -e

if [ "$EUID" -ne 0 ]; then
   echo "Please run as root"
   exit 1
fi

# Check python3
if [ -z "$(which python3)" ]; then
   echo "Please install python3"
   exit 1
fi

sudo apt install curl python3-venv

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Clean up
sudo bash clean.sh

# Run server
if [ "$1" == "--node" ]; then
   cd src/node
   python3 server.py
else
   cd src/master
   python3 master.py
fi
cd ..

deactivate
