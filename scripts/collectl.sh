#!/bin/bash

# -----------------------------------------------------------------------------
# Author: Aurélien Izoulet
# Email: aurelien.izoulet@epita.fr
# Script to manage collectl service and logs
# This script performs the following tasks depending the parameter given :
# 1. install:   Installs collectl if not already installed
# 2. start:     Clears collectl logs and metrics,
#               Starts collectl service
# 4. stop:      Stops collectl service
# 5. extract:   Extracts collectl data into a raw file
# -----------------------------------------------------------------------------

# Function to install collectl if not already installed
install_collectl() {
    if ! command -v collectl &> /dev/null; then
        echo "Collectl not found. Installing..."
        sudo apt-get update
        sudo apt-get install -y collectl
    else
        echo "Collectl is already installed."
    fi
}

# Function to clear collectl logs and metrics
clear_logs() {
    echo "Clearing collectl logs and metrics..."
    sudo rm -f /var/log/collectl/*.raw
    sudo rm -f /var/log/collectl/*.gz
    echo "Logs and metrics cleared."
}

# Function to start collectl service
start_collectl() {
    echo "Starting collectl service..."
    sudo systemctl enable collectl
    sudo systemctl start collectl
    echo "Collectl service started."
}

# Function to stop collectl service
stop_collectl() {
    echo "Stopping collectl service..."
    sudo systemctl stop collectl
    sudo systemctl disable collectl
    echo "Collectl service stopped."
}

# Function to extract data into a raw file
extract_raw() {
    echo "Extracting raw data file..."
    log_dir="/var/log/collectl"
    raw_file="${log_dir}/collectl-data.raw"
    sudo gunzip -c ${log_dir}/*.gz > $raw_file
    sudo cat ${log_dir}/*.raw >> $raw_file
    sudo chown $USER:$USER $raw_file
    echo "Raw data extracted to $raw_file."
}

# Main script logic
case "$1" in
    install)
        install_collectl
        ;;
    start)
        clear_logs
        start_collectl
        ;;
    stop)
        stop_collectl
        ;;
    extract)
        extract_raw
        ;;
    *)
        echo "Usage: $0 {install|start|stop|extract}"
        exit 1
        ;;
esac
