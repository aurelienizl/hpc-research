#!/bin/bash

# -----------------------------------------------------------------------------
# Script to Prepare a Virtual Machine (VM) for Cloning
# Author: Aurélien Izoulet
# Email: aurelien.izoulet@epita.fr
# 
# Description:
# This script prepares a VM for cloning by performing the following tasks:
# 1. Checks if the script is executed as root.
# 2. Updates and upgrades the system.
# 3. Cleans up temporary files, logs, and machine-specific data.
# 4. Clears all user bash histories.
# 5. Installs and configures cloud-init for dynamic VM setup.
# 6. Removes SSH host keys.
# 7. Resets network configuration to use DHCP.
# 8. Cleans the machine ID to avoid conflicts.
# 9. Shuts down the VM after preparation.
# -----------------------------------------------------------------------------

set -e  # Exit script immediately on any command failure

# Function to check if the script is run as root
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "Error: This script must be run as root. Exiting."
        exit 1
    fi
}

# Function to update and upgrade the system
update_system() {
    echo "Updating and upgrading the system..."
    apt update && apt upgrade -y
    apt autoremove --purge -y
    apt clean
}

# Function to clean up temporary files and logs
clean_system() {
    echo "Cleaning temporary files and logs..."
    rm -rf /tmp/* /var/tmp/*
    find /var/log -type f -exec truncate -s 0 {} \;
    journalctl --vacuum-time=1s
}

# Function to clear bash history for all users
clear_history() {
    echo "Clearing bash history..."
    for user in $(cut -f1 -d: /etc/passwd); do
        > "/home/$user/.bash_history" 2>/dev/null || true
    done
    > ~/.bash_history
    history -c
}

# Function to install and configure cloud-init
setup_cloud_init() {
    echo "Installing and configuring cloud-init..."
    apt install -y cloud-init
    cat <<EOF > /etc/cloud/cloud.cfg.d/99-custom.cfg
preserve_hostname: false
EOF
    cloud-init clean
}

# Function to remove SSH host keys
remove_ssh_keys() {
    echo "Removing SSH host keys..."
    rm -f /etc/ssh/ssh_host_*
}

# Function to reset network configuration to DHCP
configure_network() {
    echo "Setting network configuration to DHCP..."
    local interface=$(ip -o link show | awk -F': ' '{print $2}' | grep -E '^e' | head -n 1)
    if [ -f /etc/network/interfaces ]; then
        sed -i "/iface $interface inet/c\iface $interface inet dhcp" /etc/network/interfaces
    fi
    rm -f /etc/udev/rules.d/70-persistent-net.rules
}

# Function to clean the machine ID
clean_machine_id() {
    echo "Cleaning machine ID..."
    truncate -s 0 /etc/machine-id
    rm -f /var/lib/dbus/machine-id
    ln -s /etc/machine-id /var/lib/dbus/machine-id
}

# Function to shut down the VM
shutdown_vm() {
    echo "Preparation complete. Shutting down the VM..."
    shutdown -h now
}

# Main script execution
check_root
update_system
clean_system
clear_history
setup_cloud_init
remove_ssh_keys
configure_network
clean_machine_id
shutdown_vm
