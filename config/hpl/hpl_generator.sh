#!/bin/bash

# -----------------------------------------------------------------------------
# Author: Aurélien Izoulet
# Email: aurelien.izoulet@epita.fr
# Script to generate HPL benchmark configuration files for different VM setups
# -----------------------------------------------------------------------------

# Function to create an HPL configuration file
generate_hpl_config() {
    local filename=$1
    local ps=$2
    local qs=$3
    local ns=$4

    cat << EOF > "$filename"
HPLinpack benchmark input file
Innovative Computing Laboratory, University of Tennessee
HPL.out      output file name (if any)
6            device out (6=stdout,7=stderr,file)
1            # of problems sizes (N)
$ns          Ns                # Utilized memory based on configuration
1            # of NBs
64           NBs               # Smaller block size due to limited cache and memory
0            PMAP process mapping (0=Row-,1=Column-major)
1            # of process grids (P x Q)
$ps          Ps                # Rows in process grid
$qs          Qs                # Columns in process grid
16.0         threshold
1            # of panel fact
2            PFACTs (0=left, 1=Crout, 2=Right)
1            # of recursive stopping criterium
4            NBMINs (>= 1)
1            # of panels in recursion
2            NDIVs
1            # of recursive panel fact.
1            RFACTs (0=left, 1=Crout, 2=Right)
1            # of broadcast
1            BCASTs (0=1rg,1=1rM,2=2rg,3=2rM,4=Lng,5=LnM)
1            # of lookahead depth
1            DEPTHs (>=0)
2            SWAP (0=bin-exch,1=long,2=mix)
64           swapping threshold
0            L1 in (0=transposed,1=no-transposed) form
0            U  in (0=transposed,1=no-transposed) form
1            Equilibration (0=no,1=yes)
8            memory alignment in double (> 0)
EOF

    echo "Generated $filename"
}

# Generate configurations for each VM setup
generate_hpl_config "hpl_1vm_12gb_12core.dat" 1 12 49500
generate_hpl_config "hpl_2vm_6gb_6core.dat" 1 6 22500
generate_hpl_config "hpl_3vm_4gb_4core.dat" 1 4 15000
generate_hpl_config "hpl_4vm_3gb_3core.dat" 1 3 12000
generate_hpl_config "hpl_6vm_2gb_2core.dat" 1 2 7500
generate_hpl_config "hpl_12vm_1gb_1core.dat" 1 1 3600

echo "All configuration files have been generated successfully."
