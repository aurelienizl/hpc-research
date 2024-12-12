import matplotlib.pyplot as plt
import numpy as np

# Example Data (replace these with your actual parsed results)
# Coop Mode Results (Bare-metal vs KVM):
# Format: { (P,Q): (bm_mean_gflops, bm_std, kvm_mean_gflops, kvm_std) }
coop_data = {
    (1,1): (4.65, 0.00, 4.61, 0.01),
    (1,2): (8.57, 0.04, 8.44, 0.01),
    (2,2): (16.44, 0.11, 16.21, 0.06),
    (2,4): (25.21, 0.07, 25.12, 0.14)
}

# Comp Mode Results (Bare-metal vs KVM) - total gflops summed over all runs:
# Format: { (P,Q): (bm_total_gflops, kvm_total_gflops) }
comp_data = {
    (1,1): (86.13, 86.50),
    (1,2): (86.36, 85.22),
    (2,2): (130.05,131.38),
    (2,4): (125.66,125.16)
}

# Scaling with Multiple VMs:
# Format: number_of_vms: (mean_gflops_p11, mean_time_p11, mean_gflops_p12, mean_time_p12)
# Insert your actual values:
scaling_data = {
    1: (4.54, 18.35, 8.43, 9.89),
    2: (3.90, 21.39, 7.40, 11.27),
    4: (2.12, 39.66, 4.13, 20.22),
    8: (0.78,107.13, 1.57, 53.29)
}

# FIGURE 1: Coop Mode Comparison
fig, ax = plt.subplots(figsize=(6,4))
labels = []
bm_g = []
kvm_g = []
for (p,q), vals in coop_data.items():
    bm_mean, bm_std, kvm_mean, kvm_std = vals
    labels.append(f"P={p},Q={q}")
    bm_g.append(bm_mean)
    kvm_g.append(kvm_mean)

x = np.arange(len(labels))
width = 0.35
ax.bar(x - width/2, bm_g, width, label='Bare-metal', color='steelblue')
ax.bar(x + width/2, kvm_g, width, label='KVM', color='orange')

ax.set_ylabel('Gflops')
ax.set_title('Coop Mode: Bare-metal vs. KVM Performance')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()
plt.tight_layout()
plt.savefig('coop_mode_comparison.png', dpi=300)


# FIGURE 2: Comp Mode Total Gflops
fig, ax = plt.subplots(figsize=(6,4))
labels = []
bm_tot = []
kvm_tot = []
for (p,q), vals in comp_data.items():
    bm_val, kvm_val = vals
    labels.append(f"P={p},Q={q}")
    bm_tot.append(bm_val)
    kvm_tot.append(kvm_val)

x = np.arange(len(labels))
ax.bar(x - width/2, bm_tot, width, label='Bare-metal', color='steelblue')
ax.bar(x + width/2, kvm_tot, width, label='KVM', color='orange')
ax.set_ylabel('Total Gflops (sum over runs)')
ax.set_title('Comp Mode: Total Gflops Bare-metal vs. KVM')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()
plt.tight_layout()
plt.savefig('comp_mode_comparison.png', dpi=300)


# FIGURE 3: Scaling with Multiple VMs
fig, ax = plt.subplots(figsize=(6,4))
vm_counts = sorted(scaling_data.keys())
p11_g = [scaling_data[v][0] for v in vm_counts]
p12_g = [scaling_data[v][2] for v in vm_counts]

ax.plot(vm_counts, p11_g, marker='o', label='(P=1,Q=1)')
ax.plot(vm_counts, p12_g, marker='s', label='(P=1,Q=2)')
ax.set_xlabel('Number of VMs')
ax.set_ylabel('Gflops')
ax.set_title('Performance Degradation as Number of VMs Increases')
ax.grid(True)
ax.legend()
plt.tight_layout()
plt.savefig('scaling_multiple_vms.png', dpi=300)

plt.show()
