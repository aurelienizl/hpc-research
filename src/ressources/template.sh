#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
   echo "Please run as root"
   exit 1
fi

echo "Starting VM template preparation..."

# 1. Create first boot script
cat > /usr/local/sbin/first-boot-init.sh << 'EOF'
#!/bin/bash

# Generate new hostname
NEW_HOSTNAME=$(openssl rand -hex 6)
hostnamectl set-hostname $NEW_HOSTNAME

# Regenerate SSH host keys
rm -f /etc/ssh/ssh_host_*
dpkg-reconfigure openssh-server

# Update the system
apt update && apt upgrade -y

# Generate new machine-id
rm -f /etc/machine-id
dbus-uuidgen --ensure=/etc/machine-id

# Configure network if needed
netplan apply

# Remove self after execution
rm -- "$0"
# Remove the systemd service
systemctl disable first-boot-init
rm /etc/systemd/system/first-boot-init.service
EOF

# Make first boot script executable
chmod +x /usr/local/sbin/first-boot-init.sh

# 2. Create systemd service for first boot
cat > /etc/systemd/system/first-boot-init.service << EOF
[Unit]
Description=First boot initialization
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/first-boot-init.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
systemctl enable first-boot-init

echo "Updating and cleaning system..."
apt update
apt upgrade -y
apt autoremove -y
apt clean

echo "Clearing logs and temporary files..."
find /var/log -type f -exec truncate -s 0 {} \;
rm -rf /tmp/*
rm -rf /var/tmp/*

echo "Removing machine-specific information..."
truncate -s 0 /etc/machine-id
rm -f /var/lib/dbus/machine-id
ln -s /etc/machine-id /var/lib/dbus/machine-id

echo "Cleaning network configuration..."
rm -f /etc/udev/rules.d/70-persistent-net.rules
rm -f /lib/udev/rules.d/75-persistent-net-generator.rules

cat > /etc/netplan/00-template.yaml << EOF
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
EOF

echo "Clearing bash history..."
cat /dev/null > ~/.bash_history
history -c

if [ -f /etc/cloud/cloud.cfg ]; then
   echo "Cleaning cloud-init..."
   cloud-init clean --logs
fi

sudo ufw disable

echo "Template preparation complete!"
echo "The system will shutdown in 10 seconds..."
sleep 10
shutdown -h now