#!/bin/bash
# -----------------------------------------------------------------------------
# Author: Aurélien Izoulet (Refactored)
# Email: aurelien.izoulet@epita.fr
# Script to install and set up HPC-RESEARCH, including HPL and Collectl,
# and creates a user 'hpc-research' with a random password.
# -----------------------------------------------------------------------------

set -e  # Exit immediately if a command exits with a non-zero status

# -----------------------------------------------------------------------------
# Logging Function
# -----------------------------------------------------------------------------
log() {
    echo "[$(date)] $1"
}

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

package_installed() {
    dpkg -s "$1" >/dev/null 2>&1
}

# -----------------------------------------------------------------------------
# User Creation Function
# -----------------------------------------------------------------------------

create_user_if_needed() {
    local username="hpc-research"
    if id "$username" &>/dev/null; then
        log "User '$username' already exists."
    else
        log "User '$username' does not exist. Creating user..."
        # Generate a random password
        local password
        password=$(openssl rand -base64 12)

        # Create the user and set the password
        sudo useradd -m "$username"
        echo "${username}:${password}" | sudo chpasswd

        log "User '$username' created with password: $password"
        log "Please record this password securely."
    fi
}

# -----------------------------------------------------------------------------
# Collectl Installation Function
# -----------------------------------------------------------------------------

is_collectl_installed() {
    command -v collectl &> /dev/null
}

install_collectl() {
    log "Checking if Collectl is installed..."

    if command -v collectl &> /dev/null; then
        log "Collectl is already installed."
        cd ~
        return 0
    fi

    log "Collectl not found. Proceeding with installation..."

    local version="4.3.1"
    local tarball="collectl-${version}.src.tar.gz"
    local download_url="https://kumisystems.dl.sourceforge.net/project/collectl/collectl/collectl-${version}/${tarball}"
    local download_path="/tmp/${tarball}"
    local extract_dir="/tmp/collectl-${version}"

    [ -f "$download_path" ] && sudo rm -f "$download_path"

    log "Downloading Collectl ${version} source tarball..."
    if ! sudo curl -L "$download_url" -o "$download_path"; then
        log "Error: Failed to download Collectl tarball."
        cd ~
        return 1
    fi

    log "Extracting Collectl ${version} tarball..."
    if ! sudo tar -xvzf "$download_path" -C /tmp; then
        log "Error: Failed to extract Collectl tarball."
        cd ~
        return 1
    fi

    if [ -d "$extract_dir" ]; then
        cd "$extract_dir" || { log "Error: Cannot change directory to $extract_dir"; cd ~; return 1; }
    else
        log "Error: Extracted directory $extract_dir not found."
        cd ~
        return 1
    fi

    log "Running Collectl installation..."
    if ! sudo bash INSTALL; then
        log "Error: Collectl installation failed."
        cd ~
        return 1
    fi

    log "Cleaning up installation files..."
    sudo rm -f "$download_path"
    sudo rm -rf "$extract_dir"

    log "Collectl installation completed successfully."
    cd ~
}

# -----------------------------------------------------------------------------
# HPL Utility and Dependency Functions
# -----------------------------------------------------------------------------

is_hpl_installed() {
    if [ -f "/usr/local/hpl/bin/xhpl" ]; then
        log "HPL binary found."
        return 0
    fi
    return 1
}

required_dependencies=(
    build-essential
    gfortran
    wget
    make
    openmpi-bin
    libopenmpi-dev
    libblas-dev
    liblapack-dev
)

check_dependencies() {
    log "Checking for required dependencies..."
    local missing=0

    for pkg in "${required_dependencies[@]}"; do
        if ! package_installed "$pkg"; then
            log "Missing dependency: $pkg"
            missing=1
        fi
    done

    if [ $missing -eq 1 ]; then
        return 1
    fi

    log "All dependencies are installed."
    return 0
}

install_dependencies() {
    log "Installing dependencies..."
    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y "${required_dependencies[@]}"
    else
        log "Error: Unsupported package manager"
        exit 1
    fi
    cd ~
}

install_hpl() {
    local current_dir
    current_dir=$(pwd)
    local hpl_tarball="hpl-2.3.tar.gz"
    local hpl_dir="hpl-2.3"

    log "Installing HPL..."
    cd /tmp

    [ -f "$hpl_tarball" ] && rm -f "$hpl_tarball"
    wget "https://www.netlib.org/benchmark/hpl/${hpl_tarball}"
    tar -xzf "$hpl_tarball"
    cd "$hpl_dir"

    ./configure \
        LDFLAGS="-L../lapack-3.11.0" \
        LIBS="-llapack -lblas" \
        CC=mpicc \
        --prefix=/usr/local/hpl

    make -j"$(nproc)"
    sudo make install

    sudo cp /usr/local/hpl/bin/xhpl /usr/bin/

    log "HPL installation completed."
    cd ~
}

cleanup() {
    log "Cleaning up temporary files..."
    rm -rf /tmp/lapack-3.11.0* /tmp/hpl-2.3* 
    cd ~
}

# -----------------------------------------------------------------------------
# Main Execution Flow
# -----------------------------------------------------------------------------

main() {
    log "Updating package list and installing essential packages..."
    sudo apt-get update 
    sudo apt-get install -y python3 python3-venv git curl openssl

    create_user_if_needed

    log "Checking if Collectl is already installed..."
    if is_collectl_installed; then
        log "Collectl is already installed."
    else
        log "Collectl is not installed. Installing Collectl..."
        install_collectl
    fi

    log "Checking if HPL is already installed..."
    if is_hpl_installed && check_dependencies; then
        log "HPL and all dependencies are already installed."
    else
        log "HPL or dependencies missing. Installing HPL and dependencies..."
        install_dependencies
        install_hpl
        cleanup
    fi
}

main
