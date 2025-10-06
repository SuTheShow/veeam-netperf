# veeam-netperf
A lightweight, zero-dependency Python 3.13 CLI tool for parsing Veeam component logs. It scans raw .log files or entire folders, identifies network bottlenecks, transfer speeds, retries, and WAN cache hit rates, and exports the results into structured CSV reports for quick analysis and visualization.
# ⚡ Veeam NetPerf Parser

A lightweight **Python 3.13** CLI tool to analyze **Veeam component logs** (VBR, Proxy, Repository, WAN Accelerator).  
It extracts **network performance metrics**, **retry counts**, and **WAN cache hit rates**, exporting them into structured CSV files for easy review or visualization.

---

## 🚀 Features
✅ Parse `.log` files or entire Veeam log folders recursively  
✅ Auto-detect metrics:
- **Transferred** — bytes and duration
- **Bottleneck: Network** — network bottleneck %
- **WAN Accelerator cache hit** — cache hit ratio
- **Retries** — retry attempts  
✅ Automatically names output CSV after the log folder (e.g. `LABVEEAM01.CONTOSO.CSV`)  
✅ Works offline — no dependencies, no database required  

---

## 🧰 Requirements
- **Python 3.13+**
- Works on Windows PowerShell / CMD
- No external libraries required

---

## 🧩 Installation
1. Clone or download the repo:
   ```bash
   git clone https://github.com/<your-username>/veeam-netperf.git
   cd veeam-netperf
