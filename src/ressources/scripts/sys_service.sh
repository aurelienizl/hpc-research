set -e 

source "$(dirname "$0")/log.sh"

required_libs=( 
    openssl
    useradd
    chpasswd
    systemctl
)

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
        useradd -m "$username"
        echo "${username}:${password}" | chpasswd

        echo "${username}:${password}" > password.txt
        log "User '$username' created with password: $password"
        log "Please record this password securely."
        chmod 600 password.txt
    fi
}

create_startup_script() {
    cat > /usr/local/sbin/hpc-init.sh << 'EOF'

    #!/bin/bash

    sleep 10

    echo "Changing to /tmp directory..."
    cd /tmp || {
        echo "ERROR: Failed to change to /tmp directory"
        exit 1
    }

    echo "Removing old hpc-research directory if exists..."
    rm -rf hpc-research

    git clone https://github.com/aurelienizl/hpc-research.git
    if [ $? -ne 0 ]; then
        echo "ERROR: Git clone failed"
        exit 1
    fi

    cd hpc-research || {
        echo "ERROR: Failed to change to hpc-research directory"
        exit 1
    }

    git checkout dev
    if [ $? -ne 0 ]; then
        echo "ERROR: Git checkout failed"
        exit 1
    fi

    bash run.sh
    if [ $? -ne 0 ]; then
        echo "ERROR: run.sh failed"
        exit 1
    fi

    echo "HPC initialization completed successfully"
EOF

    chmod +x /usr/local/sbin/hpc-init.sh

    cat > /etc/systemd/system/hpc-init.service << EOF
    [Unit]
    Description=HPC Research Initialization
    After=network-online.target
    Wants=network-online.target
    After=systemd-resolved.service
    After=NetworkManager.service

    [Service]
    Type=simple
    User=hpc-research
    ExecStart=/bin/bash -c '/usr/local/sbin/hpc-init.sh &'
    RemainAfterExit=yes
    TimeoutStartSec=900
    Restart=on-failure
    RestartSec=30
    StartLimitBurst=3

    [Install]
    WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable hpc-init.service
}