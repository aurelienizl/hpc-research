set -e 

source "$(dirname "$0")/ext_log.sh"

required_libs=( 
    libpcre3
    wget
    build-essential 
    hwloc 
    libhwloc-dev 
    libevent-dev 
    gfortran
    git
)

openblas_url="https://github.com/xianyi/OpenBLAS.git"

install_openblas() {
    log "Installing OpenBLAS..."

    ## No check for openblas, as it is not a binary

    install_dependencies

    cd /tmp

    [ -d "OpenBLAS" ] && rm -rf "OpenBLAS"
    git clone "$openblas_url"
    cd OpenBLAS
    git checkout v0.3.17
    make -j"$(nproc)" all
    make PREFIX=/hpc/OpenBLAS install 

    log "OpenBLAS installed successfully."
}

install_openblas