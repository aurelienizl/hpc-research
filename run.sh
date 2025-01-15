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
if [ "$1" == "--node" ]; then
   cd src/node
   python3 server.py
else
   cd src/master
   python3 master.py
fi
cd ..

deactivate
