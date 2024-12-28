#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

if [ -z "$(which apt-get)" ]
  then echo "This script is only for Ubuntu/Debian systems"
  exit
fi

sudo bash clean.sh

# Update package list and upgrade all packages
sudo apt-get update && sudo apt-get upgrade -y

# Install python3 and python3-flask
sudo apt-get install -y python3 python3-flask python3-requests python3-psutil

# Verify installation
python3 --version
flask --version
