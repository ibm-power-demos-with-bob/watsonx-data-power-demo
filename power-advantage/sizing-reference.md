# 📐 watsonx.data on IBM Power — Hardware Sizing & Topology Reference

---

## 1. Node Types & Conversion Ratios

Under Red Hat OpenShift on IBM Power, watsonx.data is deployed across virtualized Logical Partitions (LPARs) managed by PowerVM:

| Plane | Node Type | x86 Sizing | IBM Power (SMT4) LPAR Spec |
|---|---|---|---|
| **Compute Plane** | Worker Nodes (Presto / Spark / Core) | 64 vCPU, 256 GB RAM | **16 Cores (vCPU ÷ 4)**, 256 GB RAM |
| **Control Plane** | Master Nodes (×3) | 8 vCPU, 32 GB RAM | **1 Core (vCPU ÷ 8)**, 32 GB RAM |
| **Infra Plane** | Helper / Bastion Node (×1) | 8 vCPU, 32 GB RAM | **1 Core (vCPU ÷ 8)**, 32 GB RAM |
| **Storage Plane** | Object Storage / Ceph (×2) | 16 vCPU, 64 GB RAM | **2 Cores (vCPU ÷ 8)**, 64 GB RAM |

*Note: Sizing includes a standard 5% headroom factor for dynamic scaling.*

---

## 2. Example Medium-Sized Deployment Topology

For a standard enterprise analytics deployment running 5 Compute Workers:
- **Total Worker vCPUs on x86:** 320 vCPU
- **Total Physical Cores on Power:** `(320 ÷ 4) + Control Plane (3 + 1 + 4) = 88 Cores`
- **Recommended Server:** IBM Power10 E1080 / S1024 or IBM Power11.
