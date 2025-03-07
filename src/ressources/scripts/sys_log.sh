log() {
    local message="[$(date)] $1"
    echo "$message" | tee -a log.txt
}

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