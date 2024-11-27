#!/bin/bash

# -----------------------------------------------------------------------------
# Author: Aurélien Izoulet
# Email: aurelien.izoulet@epita.fr
# Script to manage Collectl with unique IDs for HPC benchmarking sessions
# Compatible with Ubuntu and Debian
# Usage:
#   ./collectl_manager.sh install - to install Collectl
#   ./collectl_manager.sh start -id <id> [-o|--output <file>] [-cmd|--command <command>] - to start Collectl with a unique ID and custom command
#   ./collectl_manager.sh stop -id <id> - to stop Collectl using the ID
# -----------------------------------------------------------------------------

set -e  # Exit on any error

# Global Variables
COMMAND=""
ID=""
OUTPUT_FILE=""
CUSTOM_COMMAND="-oT -scCdmn --export lexpr"  # Default Collectl command
PID_DIR="/tmp/collectl_pids"  # Directory for managing process IDs
LOG_SCRIPT="log/log.sh"  # Path to the log script

# Function to parse arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -id)
                ID="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            -cmd|--command)
                CUSTOM_COMMAND="$2"
                shift 2
                ;;
            install|start|stop)
                COMMAND="$1"
                shift
                ;;
            *)
                "$LOG_SCRIPT" error "Unknown argument: $1"
                "$LOG_SCRIPT" info "Usage: $0 {install|start -id <id> [-o|--output <file>] [-cmd|--command <command>]|stop -id <id>}"
                exit 1
                ;;
        esac
    done
}

# Function to install Collectl
install_collectl() {
    "$LOG_SCRIPT" info "Checking if Collectl is installed..."
    if ! command -v collectl &> /dev/null; then
        "$LOG_SCRIPT" info "Collectl is not installed. Installing now..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y collectl
            "$LOG_SCRIPT" info "Collectl installation completed."
        else
            "$LOG_SCRIPT" error "Unsupported package manager"
            exit 1
        fi
    else
        "$LOG_SCRIPT" info "Collectl is already installed."
    fi
}

# Function to start Collectl
start_collectl() {
    if [[ -z "$ID" ]]; then
        "$LOG_SCRIPT" error "ID is required to start Collectl."
        "$LOG_SCRIPT" info "Usage: $0 start -id <id> [-o|--output <file>] [-cmd|--command <command>]"
        exit 1
    fi

    PID_FILE="$PID_DIR/$ID.pid"

    # Check if ID is already in use
    if [[ -f "$PID_FILE" ]]; then
        "$LOG_SCRIPT" error "ID '$ID' is already in use. Please use a different ID."
        exit 1
    fi

    # Default output file if not specified
    if [[ -z "$OUTPUT_FILE" ]]; then
        OUTPUT_FILE="$(pwd)/collectl_results_${ID}_$(date +%Y%m%d_%H%M%S).lexpr"
    fi

    "$LOG_SCRIPT" info "Starting Collectl with ID '$ID'..."

    # Check if Collectl is installed
    if ! command -v collectl &> /dev/null; then
        "$LOG_SCRIPT" error "Collectl is not installed. Run '$0 install' to install it."
        exit 1
    fi

    # Start Collectl in the background
    mkdir -p "$PID_DIR"
    nohup collectl $CUSTOM_COMMAND > "$OUTPUT_FILE" 2>&1 &
    COLLECTL_PID=$!
    echo $COLLECTL_PID > "$PID_FILE"

    "$LOG_SCRIPT" info "Collectl is now running with ID '$ID' and PID $COLLECTL_PID. Results are being saved to $OUTPUT_FILE"
}

# Function to stop Collectl
stop_collectl() {
    if [[ -z "$ID" ]]; then
        "$LOG_SCRIPT" error "ID is required to stop Collectl."
        "$LOG_SCRIPT" info "Usage: $0 stop -id <id>"
        exit 1
    fi

    PID_FILE="$PID_DIR/$ID.pid"

    if [[ -f "$PID_FILE" ]]; then
        COLLECTL_PID=$(cat "$PID_FILE")
        if ps -p $COLLECTL_PID > /dev/null; then
            "$LOG_SCRIPT" info "Stopping Collectl with ID '$ID' and PID $COLLECTL_PID..."
            kill $COLLECTL_PID
            rm "$PID_FILE"
            "$LOG_SCRIPT" info "Collectl with ID '$ID' has been stopped."
        else
            "$LOG_SCRIPT" error "Process with ID '$ID' is not running."
            rm "$PID_FILE"
            exit 1
        fi
    else
        "$LOG_SCRIPT" error "No Collectl process found with ID '$ID'."
        exit 1
    fi
}

# Main script logic
parse_arguments "$@"

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
        "$LOG_SCRIPT" info "Usage: $0 {install|start -id <id> [-o|--output <file>] [-cmd|--command <command>]|stop -id <id>}"
        exit 1
        ;;
esac
