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

set -e # Exit on any error

# Global Variables
COMMAND=""
ID=""
OUTPUT_FILE=""
CUSTOM_COMMAND="-oT -scCdmn --export lexpr" # Default Collectl command
PID_DIR="/tmp/collectl_pids"                # Directory for managing process IDs

# Function to parse arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
        -id)
            ID="$2"
            shift 2
            ;;
        -o | --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -cmd | --command)
            CUSTOM_COMMAND="$2"
            shift 2
            ;;
        install | start | stop)
            COMMAND="$1"
            shift
            ;;
        *)
            echo "Error: Unknown argument: $1"
            echo "Usage: $0 {install|start -id <id> [-o|--output <file>] [-cmd|--command <command>]|stop -id <id>}"
            exit 1
            ;;
        esac
    done
}

# Function to start Collectl
start_collectl() {
    if [[ -z "$ID" ]]; then
        echo "Error: ID is required to start Collectl."
        echo "Usage: $0 start -id <id> [-o|--output <file>] [-cmd|--command <command>]"
        exit 1
    fi

    PID_FILE="$PID_DIR/$ID.pid"

    # Check if ID is already in use
    if [[ -f "$PID_FILE" ]]; then
        echo "Error: ID '$ID' is already in use. Please use a different ID."
        exit 1
    fi

    # Default output file if not specified
    if [[ -z "$OUTPUT_FILE" ]]; then
        OUTPUT_FILE="$(pwd)/collectl_results_${ID}_$(date +%Y%m%d_%H%M%S).lexpr"
    fi

    echo "Starting Collectl with ID '$ID'..."

    # Check if Collectl is installed
    if ! command -v collectl &>/dev/null; then
        echo "Error: Collectl is not installed. Run '$0 install' to install it."
        exit 1
    fi

    # Start Collectl in the background
    mkdir -p "$PID_DIR"
    nohup collectl $CUSTOM_COMMAND >"$OUTPUT_FILE" 2>&1 &
    COLLECTL_PID=$!
    echo $COLLECTL_PID >"$PID_FILE"

    echo "Collectl is now running with ID '$ID' and PID $COLLECTL_PID. Results are being saved to $OUTPUT_FILE"
}

# Function to stop Collectl
stop_collectl() {
    if [[ -z "$ID" ]]; then
        echo "Error: ID is required to stop Collectl."
        echo "Usage: $0 stop -id <id>"
        exit 1
    fi

    PID_FILE="$PID_DIR/$ID.pid"

    if [[ -f "$PID_FILE" ]]; then
        COLLECTL_PID=$(cat "$PID_FILE")
        if ps -p $COLLECTL_PID >/dev/null; then
            echo "Stopping Collectl with ID '$ID' and PID $COLLECTL_PID..."
            kill $COLLECTL_PID
            rm "$PID_FILE"
            echo "Collectl with ID '$ID' has been stopped."
        else
            echo "Error: Process with ID '$ID' is not running."
            rm "$PID_FILE"
            exit 1
        fi
    else
        echo "Error: No Collectl process found with ID '$ID'."
        exit 1
    fi
}

# Main script logic
parse_arguments "$@"

case $COMMAND in
start)
    start_collectl
    ;;
stop)
    stop_collectl
    ;;
*)
    echo "Usage: $0 {install|start -id <id> [-o|--output <file>] [-cmd|--command <command>]|stop -id <id>}"
    exit 1
    ;;
esac
