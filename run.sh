#! /bin/bash

set -e

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Clean up
sudo bash clean.sh

# Run server
if [ "$1" == "--master" ]; then
   cd src/master
   python3 main.py
else
   cd src/node
   python3 server.py
fi

deactivate
