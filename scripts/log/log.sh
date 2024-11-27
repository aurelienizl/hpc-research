#!/bin/bash

# -----------------------------------------------------------------------------
# Author: Aurélien Izoulet
# Email: aurelien.izoulet@epita.fr
# Log script for HPC benchmarking sessions
# This script handles logging for multiple scripts in a multithreaded environment
# Usage:
#   ./log.sh <level> <message>
# Levels:
#   info    - Information messages
#   warning - Warning messages
#   error   - Error messages
# -----------------------------------------------------------------------------

# Global Variables
LOG_FILE="hpl_benchmark.log"  # Default log file
LOG_LEVELS=("info" "warning" "error")  # Supported log levels

# ANSI color codes
RESET="\e[0m"
RED="\e[31m"
YELLOW="\e[33m"

# Function to log messages
log_message() {
    local level="$1"
    local message="$2"
    local timestamp="$(date +"%Y-%m-%d %H:%M:%S")"
    local pid="$$"
    local thread_id="$(get_thread_id)"

    # Check if level is valid
    if [[ ! " ${LOG_LEVELS[@]} " =~ " $level " ]]; then
        echo "Invalid log level: $level" >&2
        exit 1
    fi

    # Format the log message
    local log_entry="[$timestamp] [$level] [PID: $pid] [THREAD: $thread_id] $message"

    # Append to the log file
    echo "$log_entry" >> "$LOG_FILE"

    # Print the log message to stdout with appropriate color
    case "$level" in
        "error")
            echo -e "${RED}$log_entry${RESET}"
            ;;
        "warning")
            echo -e "${YELLOW}$log_entry${RESET}"
            ;;
        *)
            echo "$log_entry"
            ;;
    esac
}

# Function to get thread ID
get_thread_id() {
    # Get thread ID to support multithreaded environment
    echo "$(awk '{print $2}' /proc/self/stat)"
}

# Main script logic
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <level> <message>"
    exit 1
fi

# Log the message
log_message "$1" "$2"
