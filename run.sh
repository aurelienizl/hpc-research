#! usr/bin/env

set -e

# Create and activate virtual environment
python3 -m venv /tmp/venv
source /tmp/venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Clean up
bash clean.sh

# Run server
if [ "$1" == "--master" ]; then
   cd src/server
   python3 server.py
else
   cd src/client
   python3 client.py
fi

deactivate
