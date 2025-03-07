# This is the entry point

source "$(dirname "$0")/ext_log.sh"

# Check if the script is run as root
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# Check if the script is run on Ubuntu or Debian
if [ -f /etc/debian_version ]; then
    echo "Debian-based distribution detected."
else
    echo "This script is only supported on Debian-based systems."
    exit
fi

## LIBRARY SCRIPTS ###
#                    #
#                    #
######################
log "Executing lib scripts..."

log "Executing lib_openmpi.sh..."
sudo bash lib_openmpi.sh

log "Executing lib_openblas.sh..."
sudo bash lib_openblas.sh

#### APPS SCRIPTS ####
#                    #
#                    #
######################
log "Executing app scripts..."

log "Executing app_netpipe.sh..."
sudo bash app_netpipe.sh

log "Executing app_collectl.sh..."
sudo bash app_collectl.sh

log "Executing app_hpl.sh..."
sudo bash app_hpl.sh

### SYSTEM SCRIPTS ###
#                    #
#                    #
######################
log "Executing sys scripts..."

log "Executing sys_service.sh..."
sudo bash sys_service.sh

