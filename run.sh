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

sudo apt update && sudo apt install python3-venv -y

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Clean up
sudo bash clean.sh

# Run server
cd src
python3 server.py
cd ..

deactivate
