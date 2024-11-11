#!/bin/bash

# -----------------------------------------------------------------------------
# Author: Aurélien Izoulet
# Email: aurelien.izoulet@epita.fr
# Script to automate HPL and Collectl setup and execution for benchmarking
# This script runs hpl.sh as root to set up HPL, installs collectl via collectl.sh,
# downloads the PROCESS.txt for process configuration, and coordinates HPL and Collectl runs.
# -----------------------------------------------------------------------------

set -e  # Exit on any error

# Allow Open MPI to run as root
export OMPI_ALLOW_RUN_AS_ROOT=1
export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

# Paths to scripts
HPL_SETUP_SCRIPT="./hpl.sh"
COLLECTL_SCRIPT="./collectl.sh"

disable_sleep() {
    echo "Disabling sleep, suspend, hibernate, and hybrid-sleep..."
    sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
}

# Function to run hpl.sh as root to set up HPL
setup_hpl() {
    echo "Running HPL setup script..."
    sudo bash $HPL_SETUP_SCRIPT
    echo "HPL setup completed."
}

# Function to install Collectl using collectl.sh
install_collectl() {
    echo "Installing Collectl..."
    bash $COLLECTL_SCRIPT install
    echo "Collectl installation completed."
}

# Function to download the process number
get_process_number() {
    echo "Downloading PROCESS.txt..."

    # Download PROCESS.txt with retry mechanism
    wget --retry-connrefused --waitretry=2 --read-timeout=20 --timeout=15 -t 5 https://git.server-paris.synology.me/aurelienizl/hpc-research/raw/branch/main/config/export/PROCESS.txt -O PROCESS.txt

    # Verify that PROCESS.txt exists and extract the process number
    if [ -f "PROCESS.txt" ]; then
        PROC_NUMBER=$(cat PROCESS.txt)
        echo "Process number for HPL: $PROC_NUMBER"
    else
        echo "Error: PROCESS.txt download failed after retries."
        echo "Please check network connectivity."
        exit 1
    fi
}

# Function to run HPL benchmark
run_hpl() {
    echo "Starting HPL benchmark..."
    cd /usr/local/hpl/bin
    mpirun -np $PROC_NUMBER ./xhpl > "hpl_output_$(date +%Y%m%d_%H%M%S).log" &
    HPL_PID=$!
    echo "HPL is running with PID $HPL_PID"
}

# Function to start Collectl
start_collectl() {
    echo "Starting Collectl monitoring..."
    bash $COLLECTL_SCRIPT start
}

# Function to stop Collectl
stop_collectl() {
    echo "Stopping Collectl monitoring..."
    bash $COLLECTL_SCRIPT stop
}

# Main workflow
main() {

    # Disable sleep, suspend, hibernate, and hybrid-sleep
    disable_sleep

    # Setup HPL and install Collectl
    setup_hpl
    install_collectl
    
    # Download process number
    get_process_number

    # Start Collectl and run HPL
    start_collectl
    run_hpl

    # Wait for HPL to complete and then stop Collectl
    wait $HPL_PID
    echo "HPL benchmark has finished."

    # Stop Collectl
    stop_collectl

    echo "Benchmark workflow completed. Results are saved in logs."
}

# Run the main function
main
