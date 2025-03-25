set -e 

source "$(dirname "$0")/ext_log.sh"

required_libs=( 
    wget
    build-essential 
)

netpipe_url="http://bitspjoule.org/netpipe/code/NetPIPE-3.7.2.tar.gz"

install_netpipe() {
    log "Installing NetPIPE..."

    if which NPmpi; then
        log "NetPIPE is already installed."
        cd ~
        return 0
    fi

    install_dependencies

    cd /tmp

    [ -f "NetPIPE-3.7.2.tar.gz" ] && rm -f "NetPIPE-3.7.2.tar.gz"
    wget "$netpipe_url"
    tar -xzf NetPIPE-3.7.2.tar.gz
    cd NetPIPE-3.7.2

    export PATH=$PATH:/hpc/OpenMPI/bin/

    # Configure NetPIPE
    sed -i 's|^MPI2_INC =.*|MPI2_INC = /hpc/OpenMPI/include|' makefile

    # Compile NetPIPE  
    make mpi

    # Move NetPIPE binary to /usr/local/bin
    sudo cp NPmpi /usr/local/bin

    log "NetPIPE installed successfully."
}

install_netpipe