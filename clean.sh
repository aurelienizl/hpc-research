#!/bin/bash

# Find and remove all __pycache__ directories
sudo find . -type d -name "__pycache__" -exec rm -r {} +

# Remove all .pytest_cache directories
sudo find . -type d -name ".pytest_cache" -exec rm -r {} +

# Find and remove all .pyc files
sudo find . -type f -name "*.pyc" -exec rm -f {} +

# Find and remove all .txt files
sudo find . -type f -name "log.txt" -exec rm -f {} +

# Find and remove all HPLConfigurations directories
sudo find . -type d -name "results" -exec rm -r {} +

# Find and remove all HPLConfigurations directories
sudo find . -type d -name "benchmarks" -exec rm -r {} +

# Remove the collectl file in /tmp/collectl_pids
sudo rm -rf /tmp/collectl_pids

# Remove the collectl file in /tmp/hpl_instance
sudo rm -rf /tmp/hpl_instance

# Kill all the running collectl processes
sudo killall collectl

# Kill all the running HPL processes
sudo killall xhpl

echo "Python project cleaned successfully."
