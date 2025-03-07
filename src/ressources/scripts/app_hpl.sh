set -e

source "$(dirname "$0")/log.sh"

required_libs=(
    gcc
    make
    wget
    gfortran
    wget
    make
    libblas-dev
    liblapack-dev
)

hpl_url="https://www.netlib.org/benchmark/hpl/hpl-2.3.tar.gz"

install_dependencies() {
    log "Installing dependencies..."

    if which apt-get; then
        sudo apt-get update
        sudo apt-get install -y "${required_libs[@]}"
    else
        log "Error: Unsupported package manager"
        exit 1
    fi
}

install_hpl() {
    log "Installing HPL..."

    if which xhpl; then
        log "HPL is already installed."
        cd ~
        return 0
    fi

    install_dependencies

    cd $HOME

    [ -f "hpl-2.3.tar.gz" ] && rm -f "hpl-2.3.tar.gz"
    [ -d "hpl" ] && rm -rf "hpl"
    wget "$hpl_url"
    tar -xzf hpl-2.3.tar.gz
    mv hpl-2.3 hpl
    cd hpl
    cd setup
    sh make_generic
    cp Make.UNKNOWN ../Make.linux
    cd ..

    export PATH=$PATH:/hpc/OpenMPI/bin/

    # Replace the line ARCH         = UNKNOWN by ARCH         = linux
    sed -i 's/ARCH         = UNKNOWN/ARCH         = linux/g' Make.linux

    sed -i -e 's|^MPdir[[:space:]]*=.*|MPdir        = /hpc/OpenMPI|' \
       -e 's|^MPinc[[:space:]]*=.*|MPinc        = -I$(MPdir)/include|' \
       -e 's|^MPlib[[:space:]]*=.*|MPlib        = $(MPdir)/lib/libmpi.so|' Make.linux

    sed -i -e 's|^LAdir[[:space:]]*=.*|LAdir        = /hpc/OpenBLAS|' \
       -e 's|^LAinc[[:space:]]*=.*|LAinc        =|' \
       -e 's|^LAlib[[:space:]]*=.*|LAlib        = $(LAdir)/lib/libopenblas.a|' Make.linux

    make arch=linux

    log "HPL installed successfully."
}

install_hpl