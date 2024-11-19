#!/bin/bash

# -----------------------------------------------------------------------------
# Author: Aurélien Izoulet
# Email: aurelien.izoulet@epita.fr
# Script to manage Collectl for HPC benchmarking sessions
# Usage:
#   ./collectl_manager.sh install - to install Collectl
#   ./collectl_manager.sh start - to start Collectl in the background
#   ./collectl_manager.sh stop - to stop Collectl gracefully
# -----------------------------------------------------------------------------

set -e  # Exit on any error

COMMAND=$1
OUTPUT_FILE="$(pwd)/collectl_results_$(date +%Y%m%d_%H%M%S).lexpr"

install_collectl() {
    echo "Checking if Collectl is installed..."
    if ! command -v collectl &> /dev/null; then
        echo "Collectl is not installed. Installing now..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y collectl
        elif command -v yum &> /dev/null; then
            sudo yum install -y collectl
        else
            echo "Error: Unsupported package manager"
            exit 1
        fi
        echo "Collectl installation completed."
    else
        echo "Collectl is already installed."
    fi
}

start_collectl() {
    echo "Starting Collectl in the background..."

    # Check if Collectl is installed
    if ! command -v collectl &> /dev/null; then
        echo "Collectl is not installed. Run '$0 install' to install it."
        exit 1
    fi

    # Start Collectl in the background with custom options and save results to a file
    collectl -oT -scCdmn --export lexpr > "$OUTPUT_FILE" &
    COLLECTL_PID=$!
    echo $COLLECTL_PID > /tmp/collectl_pid.txt

    echo "Collectl is now running in the background with PID $COLLECTL_PID"
    echo "Results are being saved to $OUTPUT_FILE"
}

stop_collectl() {
    if [ -f "/tmp/collectl_pid.txt" ]; then
        COLLECTL_PID=$(cat /tmp/collectl_pid.txt)
        if ps -p $COLLECTL_PID > /dev/null; then
            echo "Stopping Collectl with PID $COLLECTL_PID..."
            kill $COLLECTL_PID
            rm /tmp/collectl_pid.txt
            echo "Collectl has been stopped."
        else
            echo "Collectl is not running or PID not found."
            rm /tmp/collectl_pid.txt
        fi
    else
        echo "No running Collectl process found."
    fi
}

case $COMMAND in
    install)
        install_collectl
        ;;
    start)
        start_collectl
        ;;
    stop)
        stop_collectl
        ;;
    *)
        echo "Usage: $0 {install|start|stop}"
        exit 1
        ;;
esac
