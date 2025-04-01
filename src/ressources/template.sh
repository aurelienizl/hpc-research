#!/bin/bash
# This script sets up a fresh Ubuntu 22.04 LTS server VM by configuring:
#  - The hostname (updates /etc/hostname and /etc/hosts)
#  - A static IP configuration via netplan
#
# Run this script as root.

# Ensure the script is run as root
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root. Try using sudo."
  exit 1
fi

# Prompt for input parameters
read -p "Enter new hostname: " NEW_HOSTNAME
read -p "Enter network interface (e.g., ens33): " NET_IF
read -p "Enter static IP address with CIDR (e.g., 192.168.1.100/24): " STATIC_IP
read -p "Enter gateway IP (e.g., 192.168.1.1): " GATEWAY
read -p "Enter DNS servers (comma-separated, e.g., 8.8.8.8,8.8.4.4): " DNS_SERVERS

# Strip any spaces from the DNS list (ensuring proper YAML formatting)
dns_list=$(echo "$DNS_SERVERS" | tr -d ' ')

# Update hostname
echo "$NEW_HOSTNAME" > /etc/hostname
hostnamectl set-hostname "$NEW_HOSTNAME"

# Update /etc/hosts to ensure local resolution works correctly.
# This adds or updates a line for 127.0.1.1 with the new hostname.
if grep -q "127.0.1.1" /etc/hosts; then
  sed -i "s/^127\.0\.1\.1.*/127.0.1.1 $NEW_HOSTNAME/" /etc/hosts
else
  echo "127.0.1.1 $NEW_HOSTNAME" >> /etc/hosts
fi

# Backup any existing netplan configuration file(s)
NETPLAN_DIR="/etc/netplan"
BACKUP_DIR="/etc/netplan_old/backup_$(date +%F_%T)"
mkdir -p "$BACKUP_DIR"
mv "$NETPLAN_DIR"/*.yaml "$BACKUP_DIR" 2>/dev/null

# Create a new netplan configuration file
cat > "$NETPLAN_DIR/01-netcfg.yaml" <<EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    $NET_IF:
      dhcp4: no
      addresses: [$STATIC_IP]
      gateway4: $GATEWAY
      nameservers:
        addresses: [$dns_list]
EOF

chmod 644 "$NETPLAN_DIR/01-netcfg.yaml"

netplan generate
netplan apply

echo "Configuration complete."
echo "Hostname set to: $NEW_HOSTNAME"
echo "Network interface $NET_IF configured with static IP $STATIC_IP, gateway $GATEWAY, and DNS [$dns_list]."

sudo ufw disable
echo "Firewall disabled."
echo "Please reboot the server for changes to take effect."
echo "Rebooting in 5 seconds..."
sleep 5
reboot