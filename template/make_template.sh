#!/bin/bash

# -----------------------------------------------------------------------------
# Author: Aurélien Izoulet
# Email: aurelien.izoulet@epita.fr
# Script to prepare a VM for cloning
# This script performs the following tasks:
# 1. Checks if the script is run as root
# 2. Updates and upgrades the system
# 3. Cleans up temporary files and logs
# 4. Clears bash history
# 5. Installs and configures cloud-init
# 6. Removes SSH host keys
# 7. Sets network configuration to DHCP
# 8. Cleans the machine ID
# 9. Shuts down the VM
# -----------------------------------------------------------------------------

# Function to check if the script is run as root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "This script must be run as root. Exiting."
        exit 1
    fi
}

# Update and upgrade the system
update_system() {
    echo "Updating and upgrading the system..."
    apt update && apt upgrade -y
    apt autoremove --purge -y
    apt clean
}

# Clean up temporary files and logs
clean_system() {
    echo "Cleaning temporary files and logs..."
    rm -rf /tmp/* /var/tmp/*
    truncate -s 0 /var/log/*.log
    rm -rf /var/log/*.gz /var/log/*.1 /var/log/*-???????? /var/log/*.old
    journalctl --vacuum-time=1s
}

# Clear bash history
clear_history() {
    echo "Clearing bash history..."
    cat /dev/null > ~/.bash_history && history -c
}

# Install and configure cloud-init
setup_cloud_init() {
    echo "Installing and configuring cloud-init..."
    apt install -y cloud-init
    echo "preserve_hostname: false" > /etc/cloud/cloud.cfg.d/99-custom.cfg
    cloud-init clean
}

# Remove SSH host keys
remove_ssh_keys() {
    echo "Removing SSH host keys..."
    rm -f /etc/ssh/ssh_host_*
}

# Set network configuration to DHCP
configure_network() {
    echo "Setting network configuration to DHCP..."
    if [ -f /etc/network/interfaces ]; then
        sed -i '/iface eth0 inet/c\iface eth0 inet dhcp' /etc/network/interfaces
    fi
    rm -f /etc/udev/rules.d/70-persistent-net.rules
}

# Clean the machine ID
clean_machine_id() {
    echo "Cleaning machine ID..."
    truncate -s 0 /etc/machine-id
    rm -f /var/lib/dbus/machine-id
    ln -s /etc/machine-id /var/lib/dbus/machine-id
}

# Shutdown the VM
shutdown_vm() {
    echo "Preparation complete. Shutting down the VM..."
    sudo shutdown -h now
}

# Run all functions
check_root
update_system
clean_system
clear_history
setup_cloud_init
remove_ssh_keys
configure_network
clean_machine_id
shutdown_vm
