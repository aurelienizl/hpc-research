#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# Clean up
sudo bash clean.sh

MASTER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$MASTER_IP" ]; then
  echo "Error: Unable to determine MASTER_IP. Please set it manually."
  exit 1
fi

export MASTER_IP=127.0.0.1
export MASTER_PORT=5000
export MASTER_API_KEY=123456

export API_HOST=0.0.0.0
export API_PORT=5000
export API_KEY=123456

cd src
sudo -E python3 server.py
cd ..
