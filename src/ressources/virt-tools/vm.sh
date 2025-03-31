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

echo "Processing the first $vm_count VM(s) with ${cores} CPU core(s) and ${mem_mb} MB memory..."

# Loop over the selected VMs.
for (( i=0; i<vm_count; i++ )); do
    vm=${vms[i]}
    
    echo "Shutting down $vm..."
    virsh shutdown "$vm"

    echo "Waiting for $vm to shut down..."
    # Wait until the VM is no longer running.
    while [[ "$(virsh domstate "$vm")" == "running" ]]; do
        sleep 1
    done
    echo "$vm is now shut off."

    echo "Updating $vm: setting ${cores} CPU core(s) and ${mem_mb} MB memory..."
    
    # Update CPU cores persistently.
    virsh setvcpus "$vm" "$cores" --config
    if [ $? -ne 0 ]; then
        echo "Error setting CPU cores for $vm"
    fi

    # Update memory size persistently.
    virsh setmem "$vm" "$mem_kib" --config
    if [ $? -ne 0 ]; then
        echo "Error setting memory for $vm"
    fi

    echo "Starting $vm..."
    virsh start "$vm"
done

echo "Configuration update and startup complete for the selected VMs."
