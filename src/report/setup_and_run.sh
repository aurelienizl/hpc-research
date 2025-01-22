#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Step 1: Create a virtual environment named 'venv'
python3 -m venv venv

# Step 2: Activate the virtual environment
source venv/bin/activate

# Step 3: Upgrade pip and install required packages
pip install --upgrade pip
pip install jinja2 matplotlib pandas requests
