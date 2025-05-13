set -e

source "$(dirname "$0")/ext_log.sh"

required_libs=(
    gcc
    make
    wget
)

collectl_url="https://downloads.sourceforge.net/project/collectl/collectl/collectl-4.3.1/collectl-4.3.1.src.tar.gz"

install_collectl() {
    log "Installing Collectl..."

    if wich -v collectl &> /dev/null; then
        log "Collectl is already installed."
        cd ~
        return 0
    fi

    install_dependencies

    cd /tmp

    [ -f "collectl-4.3.1.src.tar.gz" ] && rm -f "collectl-4.3.1.src.tar.gz"
    wget "$collectl_url"
    gunzip -c collectl-4.3.1.src.tar.gz | tar xf -
    cd collectl-4.3.1
    sudo chmod +x INSTALL

    # Install Collectl, handled by the INSTALL script
    sudo bash INSTALL

    log "Collectl installed successfully."
}

install_collectl