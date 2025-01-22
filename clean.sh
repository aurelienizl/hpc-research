#!/bin/bash

# Find and remove all __pycache__ directories
find . -type d -name "__pycache__" -exec rm -r {} +

# Remove all .pytest_cache directories
find . -type d -name ".pytest_cache" -exec rm -r {} +

# Find and remove all .pyc files
find . -type f -name "*.pyc" -exec rm -f {} +

# Find and remove all .txt files
find . -type f -name "log.txt" -exec rm -f {} +

# Find and remove all HPLConfigurations directories
find . -type d -name "results" -exec rm -r {} +

# Find and remove all HPLConfigurations directories
find . -type d -name "benchmarks" -exec rm -r {} +

# Find and remove all HPLConfigurations directories
find . -type d -name "venv" -exec rm -r {} +

# Remove the collectl file in /tmp/collectl_pids
rm -rf /tmp/collectl_pids

# Remove the collectl file in /tmp/hpl_instance
rm -rf /tmp/hpl_instance

# Kill all the running collectl processes
killall collectl

# Kill all the running HPL processes
killall xhpl

echo "Python project cleaned successfully."
