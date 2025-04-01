#!/bin/bash
# Usage: ./update_vm_config.sh <cpu_cores> <ram_in_MB> <number_of_vms_to_start>
# Example: ./update_vm_config.sh 2 2048 3

# Check that exactly three parameters are provided.
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <cpu_cores> <ram_in_MB> <number_of_vms_to_start>"
    exit 1
fi

cores=$1
mem_mb=$2
vm_count=$3

# Convert memory from MB to KiB (1 MB = 1024 KiB) for virsh.
mem_kib=$(( mem_mb * 1024 ))

# Define the VM names.
vms=(vm1 vm2 vm3 vm4 vm5 vm6 vm7 vm8)

# Validate that the number of VMs to process does not exceed available VMs.
if [ "$vm_count" -gt "${#vms[@]}" ]; then
    echo "Error: Only ${#vms[@]} VMs are available."
    exit 1
fi

# Shutdown all virtual machines first.
echo "Initiating shutdown for all VMs..."
for vm in "${vms[@]}"; do
    echo "Shutting down $vm..."
    virsh shutdown "$vm"
done

echo "Waiting for all VMs to shut down..."
for vm in "${vms[@]}"; do
    while [[ "$(virsh domstate "$vm")" == "running" ]]; do
        sleep 1
    done
    echo "$vm is now shut off."
done

echo "Processing the first $vm_count VM(s) with ${cores} CPU core(s) and ${mem_mb} MB memory..."

# Loop over the selected VMs to update configuration and restart them.
for (( i=0; i<vm_count; i++ )); do
    vm=${vms[i]}
    
    echo "Updating $vm: setting ${cores} CPU core(s) and ${mem_mb} MB memory..."
    
    # Dump the current XML definition.
    if ! virsh dumpxml "$vm" > "${vm}.xml"; then
        echo "Error dumping XML for $vm. Skipping update for this VM."
        continue
    fi

    # Replace the <vcpu> element so that both the inner value and the 'current' attribute match the desired CPU count.
    if ! sed -i "s|<vcpu[^>]*>[^<]*</vcpu>|<vcpu placement=\"static\" current=\"$cores\">$cores</vcpu>|" "${vm}.xml"; then
        echo "Error updating XML file for $vm. Skipping update for this VM."
        continue
    fi

    if ! virsh define "${vm}.xml"; then
        echo "Error defining updated configuration for $vm. Skipping update for this VM."
        continue
    fi

    # Update memory settings: set both maximum and current memory.
    if ! virsh setmaxmem "$vm" "$mem_kib" --config; then
        echo "Error setting max memory for $vm. Skipping update for this VM."
        continue
    fi

    if ! virsh setmem "$vm" "$mem_kib" --config; then
        echo "Error setting memory for $vm. Skipping update for this VM."
        continue
    fi

    echo "Starting $vm..."
    if ! virsh start "$vm"; then
        echo "Error starting $vm."
        continue
    fi
done

echo "Configuration update and startup complete for the selected VMs."
