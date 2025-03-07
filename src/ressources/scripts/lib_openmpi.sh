set -e

source "$(dirname "$0")/log.sh"

required_libs=( 
    libpcre3
    wget
    build-essential 
    hwloc 
    libhwloc-dev 
    libevent-dev 
    gfortran
)

openmpi_url="https://download.open-mpi.org/release/open-mpi/v5.0/openmpi-5.0.7.tar.gz"

install_openmpi() {
    log "Installing OpenMPI..."

    if which mpirun; then
        log "OpenMPI is already installed."
        cd ~
        return 0
    fi

    install_dependencies

    cd /tmp

    [ -f "openmpi-5.0.7.tar.gz" ] && rm -f "openmpi-5.0.7.tar.gz"
    wget "$openmpi_url"
    gunzip -c openmpi-5.0.7.tar.gz | tar xf -
    cd openmpi-5.0.7
    ./configure --prefix=/hpc/OpenMPI
    make -j"$(nproc)"
    make install

    log "OpenMPI installed successfully."
}

install_openmpi