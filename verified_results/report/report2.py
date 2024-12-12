import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

cpu_model = "Intel Core i9-9900KF (8C/16T)"

# Dummy Data Structures: Replace with actual parsed results
# Suppose you have dictionaries like before for coop_data and comp_data:
# coop_data[(P,Q)] = (bm_mean_gflops, bm_std, kvm_mean_gflops, kvm_std)
# comp_data[(P,Q)] = (bm_total_gflops, kvm_total_gflops)
coop_data = {
    (1, 1): (4.65, 0.00, 4.61, 0.01),
    (1, 2): (8.57, 0.04, 8.44, 0.01),
    (2, 2): (16.44, 0.11, 16.21, 0.06),
    (2, 4): (25.21, 0.07, 25.12, 0.14),
}

comp_data = {
    (1, 1): (86.13, 86.50),
    (1, 2): (86.36, 85.22),
    (2, 2): (130.05, 131.38),
    (2, 4): (125.66, 125.16),
}

# Cluster scaling data (P=1,Q=1) and (P=1,Q=2) from previous scenario
# Format: {num_vms: (gflops_p11, time_p11, gflops_p12, time_p12)}
scaling_data = {
    1: (4.54, 18.35, 8.43, 9.89),
    2: (3.90, 21.39, 7.40, 11.27),
    4: (2.12, 39.66, 4.13, 20.22),
    8: (0.78, 107.13, 1.57, 53.29),
}

########################################
# Ratio Comparison (Coop mode)
########################################
# Plot ratio KVM/BM for coop mode
fig, ax = plt.subplots(figsize=(6, 4))
labels = []
ratios = []
for (p, q), vals in coop_data.items():
    bm_mean, bm_std, kvm_mean, kvm_std = vals
    ratio = kvm_mean / bm_mean
    labels.append(f"P={p},Q={q}")
    ratios.append(ratio)

x = np.arange(len(labels))
ax.bar(x, ratios, color="purple")
ax.axhline(y=1.0, color="black", linestyle="--")
ax.set_ylabel("KVM/BM Gflops Ratio")
ax.set_title(f"Coop Mode Virtualization Overhead Ratio on {cpu_model}")
ax.set_xticks(x)
ax.set_xticklabels(labels)
plt.tight_layout()
plt.savefig("coop_mode_ratio.png", dpi=300)

########################################
# Ratio Comparison (Comp mode)
########################################
fig, ax = plt.subplots(figsize=(6, 4))
labels = []
ratios = []
for (p, q), vals in comp_data.items():
    bm_g, kvm_g = vals
    ratio = kvm_g / bm_g
    labels.append(f"P={p},Q={q}")
    ratios.append(ratio)

x = np.arange(len(labels))
ax.bar(x, ratios, color="green")
ax.axhline(y=1.0, color="black", linestyle="--")
ax.set_ylabel("KVM/BM Total Gflops Ratio")
ax.set_title(f"Comp Mode Virtualization Overhead Ratio on {cpu_model}")
ax.set_xticks(x)
ax.set_xticklabels(labels)
plt.tight_layout()
plt.savefig("comp_mode_ratio.png", dpi=300)

########################################
# Efficiency Plot for Cluster Scaling
# Efficiency = Gflops per VM, to see how efficiency drops as we add VMs
########################################
vm_counts = sorted(scaling_data.keys())
p11_g = np.array([scaling_data[v][0] for v in vm_counts])
p12_g = np.array([scaling_data[v][2] for v in vm_counts])

p11_eff = p11_g / vm_counts
p12_eff = p12_g / vm_counts

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(vm_counts, p11_eff, marker="o", label="(P=1,Q=1) Efficiency")
ax.plot(vm_counts, p12_eff, marker="s", label="(P=1,Q=2) Efficiency")

# Set axis limits to start from zero
ax.set_xlim(0, max(vm_counts) + 1)  # Start x-axis from zero
ax.set_ylim(
    0, max(max(p11_eff), max(p12_eff)) * 1.1
)  # Start y-axis from zero, add 10% padding

ax.set_xlabel("Number of VMs")
ax.set_ylabel("Gflops per VM")
ax.set_title(f"Efficiency Degradation with More VMs on {cpu_model}")
ax.grid(True)
ax.legend()
plt.tight_layout()
plt.savefig("efficiency_degradation.png", dpi=300)


########################################
# Ratio of cluster performance to single-VM performance
########################################
p11_baseline = scaling_data[1][0]
p12_baseline = scaling_data[1][2]

p11_ratio = p11_g / p11_baseline
p12_ratio = p12_g / p12_baseline

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(vm_counts, p11_ratio, marker="o", label="(P=1,Q=1)")
ax.plot(vm_counts, p12_ratio, marker="s", label="(P=1,Q=2)")
ax.set_xlabel("Number of VMs")
ax.set_ylabel("Fraction of Single-VM Performance")
ax.set_title("Relative Performance with Increasing VM Count")
ax.axhline(y=1.0, color="black", linestyle="--", label="Single-VM baseline")
ax.grid(True)
ax.legend()
plt.tight_layout()
plt.savefig("relative_performance_cluster.png", dpi=300)

########################################
# Scatter plot: Gflops vs Time for a scenario
# Let's pick Coop (P=2,Q=4) from BM and KVM to show distribution
########################################
# Suppose we have lists of run results for a given scenario (P=2,Q=4)
# Replace with actual parsed run-level data if available.
# Here we just simulate random data to show how you'd do it:

# Example simulated data:
bm_runs_g = [25.1, 25.2, 25.3, 25.1, 25.05]
bm_runs_t = [3.31, 3.33, 3.30, 3.32, 3.31]
kvm_runs_g = [25.12, 25.08, 25.20, 25.10, 25.09]
kvm_runs_t = [3.32, 3.34, 3.31, 3.35, 3.33]

fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(bm_runs_t, bm_runs_g, color="blue", alpha=0.7, label="Bare-metal")
ax.scatter(kvm_runs_t, kvm_runs_g, color="red", alpha=0.7, label="KVM")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Gflops")
ax.set_title(f"Performance Distribution: (P=2,Q=4) Coop Mode on {cpu_model}")
ax.grid(True)
ax.legend()
plt.tight_layout()
plt.savefig("scatter_time_gflops.png", dpi=300)

plt.show()

########################################
# Heatmap (Optional, if you have a grid of P,Q)
# If you have data for a regular grid of P,Q (e.g., P in {1,2,4}, Q in {1,2,4}),
# you can create a 2D array and plot using seaborn heatmap.

# Example (P,Q) sets
# Suppose you have a nice grid: P_vals = [1,2,4], Q_vals=[1,2,4]
# Construct arrays
P_vals = [1, 2, 4]
Q_vals = [1, 2, 4]
# Example data: Just re-use coop_data or comp_data if it covers these points.
# You must ensure all (P,Q) combos exist.
heatmap_array_bm = np.array(
    [
        [coop_data[(p, q)][0] if (p, q) in coop_data else np.nan for q in Q_vals]
        for p in P_vals
    ]
)
heatmap_array_kvm = np.array(
    [
        [coop_data[(p, q)][2] if (p, q) in coop_data else np.nan for q in Q_vals]
        for p in P_vals
    ]
)

fig, ax = plt.subplots(figsize=(5, 4))
sns.heatmap(
    heatmap_array_bm,
    annot=True,
    xticklabels=Q_vals,
    yticklabels=P_vals,
    cmap="viridis",
    ax=ax,
)
ax.set_title(f"Bare-metal Coop Gflops Heatmap on {cpu_model}")
ax.set_xlabel("Q")
ax.set_ylabel("P")
plt.tight_layout()
plt.savefig("baremetal_coop_heatmap.png", dpi=300)

fig, ax = plt.subplots(figsize=(5, 4))
sns.heatmap(
    heatmap_array_kvm,
    annot=True,
    xticklabels=Q_vals,
    yticklabels=P_vals,
    cmap="viridis",
    ax=ax,
)
ax.set_title(f"KVM Coop Gflops Heatmap on {cpu_model}")
ax.set_xlabel("Q")
ax.set_ylabel("P")
plt.tight_layout()
plt.savefig("kvm_coop_heatmap.png", dpi=300)

plt.show()
