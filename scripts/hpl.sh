#!/bin/bash

# -----------------------------------------------------------------------------
# Author: Aurélien Izoulet
# Email: aurelien.izoulet@epita.fr
# Script to install and set up HPL (High-Performance Linpack)
# This script performs the following tasks:
# 1. Installs necessary dependencies (build-essential, gfortran, wget, make, openmpi)
# 2. Downloads and installs BLAS/LAPACK libraries
# 3. Downloads and installs HPL
# 4. Sets up HPL configuration file (HPL.dat)
# 5. Cleans up temporary files
# -----------------------------------------------------------------------------


#!/bin/bash

# Script to install HPL and dependencies
set -e  # Exit on any error

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "Starting HPL installation script..."

# Install required packages
install_dependencies() {
    echo "Installing dependencies..."
    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y \
            build-essential \
            gfortran \
            wget \
            make \
            openmpi-bin \
            libopenmpi-dev \
            libblas-dev \
            liblapack-dev
    elif command_exists yum; then
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y \
            gcc-gfortran \
            wget \
            openmpi-devel
    else
        echo "Error: Unsupported package manager"
        exit 1
    fi
}

# Install BLAS/LAPACK
install_blas_lapack() {

    # Save current directory
    current_dir=$(pwd)
    cd /tmp

    echo "Installing BLAS/LAPACK..."

    # Remove existing v3.12.0.tar.gz if it exists
    [ -f "v3.12.0.tar.gz" ] && rm -rf "v3.12.0.tar.gz"

    wget https://github.com/Reference-LAPACK/lapack/archive/refs/tags/v3.12.0.tar.gz
    tar -xzf v3.12.0.tar.gz
    cd lapack-3.12.0
    cp make.inc.example make.inc
    make blaslib -j${nbproc}
    make lapacklib -j${nbproc}
    cd ..

    # Return to original directory
    cd "$current_dir"
}

# Install HPL
install_hpl() {

    # Save current directory
    current_dir=$(pwd)
    cd /tmp

    echo "Installing HPL..."

    # Remove existing hpl-2.3.tar.gz if it exists
    [ -f "hpl-2.3.tar.gz" ] && rm -rf "hpl-2.3.tar.gz"

    wget https://www.netlib.org/benchmark/hpl/hpl-2.3.tar.gz
    tar -xzf hpl-2.3.tar.gz
    cd hpl-2.3

    # Configure HPL
    ./configure \
        LDFLAGS="-L../lapack-3.11.0" \
        LIBS="-llapack -lblas" \
        CC=mpicc \
        --prefix=/usr/local/hpl

    make -j${nbproc}
    sudo make install
    cd ..

    # Return to original directory
    cd "$current_dir"
}

# Setup HPL configuration
setup_hpl() {

    # Save current directory
    current_dir=$(pwd)
    cd /tmp

    echo "Setting up HPL configuration..."

    # Remove existing HPL.dat if it exists
    [ -f "HPL.dat" ] && rm "HPL.dat"

    # Download HPL.dat with retry mechanism
    wget --retry-connrefused --waitretry=2 --read-timeout=20 --timeout=15 -t 5 https://git.server-paris.synology.me/aurelienizl/hpc-research/raw/branch/main/config/export/HPL.dat -O HPL.dat

    # Check if HPL.dat was successfully downloaded
    if [ -f "HPL.dat" ]; then
        sudo mv HPL.dat /usr/local/hpl/bin/
        echo "HPL.dat successfully moved to /usr/local/hpl/bin/"
    else
        echo "Warning: HPL.dat download failed after retries."
        echo "Please check network connectivity and write permissions on /usr/local/hpl/bin/"
        exit 1
    fi

    # Return to original directory
    cd "$current_dir"
}

# Cleanup
cleanup() {
    echo "Cleaning up..."
    rm -rf lapack-3.11.0*
    rm -rf hpl-2.3*
}

# Main installation process
main() {
    install_dependencies
    install_blas_lapack
    install_hpl
    setup_hpl
    cleanup

    echo "Installation completed!"
    echo "HPL binary location: /usr/local/hpl/bin/xhpl"
    echo "To run HPL benchmark:"
    echo "cd /usr/local/hpl/bin"
    echo "mpirun -np <number_of_processes> ./xhpl"
}

# Run the installation
main
