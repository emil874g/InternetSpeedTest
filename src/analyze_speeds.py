import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

sns.set(style="whitegrid")

# Point to the CSV file in the parent directory
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "office_internet_speeds.csv")

# LOAD + CLEAN DATA
df = pd.read_csv(CSV_PATH)
# Strip whitespace from column names
df.columns = df.columns.str.strip()
# Parse Timestamp after cleaning column names
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# 1. ONLY acstation1 data
df_acstation = df[df["Device"].str.contains("acstation", case=False, na=False)].copy()

# 2. START FROM Jan 20 16:00 (skip early MacBook tests)
df_acstation = df_acstation[df_acstation["Timestamp"] >= "2026-01-20 16:00:00"]

# 3. SORT by time
df_acstation = df_acstation.sort_values("Timestamp").reset_index(drop=True)

print("Total acstation1 rows after filtering:", len(df_acstation))
print("Date range:", df_acstation["Timestamp"].min(), "to", df_acstation["Timestamp"].max())
print("\nDownload summary (acstation1 only):")
print(df_acstation["Download_Mbps"].describe())


# TIME SERIES: ACSTATION1 ONLY
plt.figure(figsize=(14, 5))
sns.lineplot(data=df_acstation, x="Timestamp", y="Download_Mbps", label="Download")
sns.lineplot(data=df_acstation, x="Timestamp", y="Upload_Mbps", label="Upload")

plt.axhline(1000, color="red", linestyle="--", label="Contracted 1000 Mbps")
plt.title("acstation1: Download/Upload over time vs contract")
plt.xlabel("Time")
plt.ylabel("Speed (Mbps)")
plt.legend()
plt.tight_layout()
plt.show()

# DISTRIBUTION: ACSTATION1 ONLY
plt.figure(figsize=(14, 5))

plt.subplot(1, 2, 1)
sns.histplot(df_acstation["Download_Mbps"], kde=True)
plt.axvline(1000, color="red", linestyle="--", label="Contract 1000")
plt.title("acstation1: Download distribution")
plt.xlabel("Download (Mbps)")
plt.legend()

plt.subplot(1, 2, 2)
sns.histplot(df_acstation["Upload_Mbps"], kde=True)
plt.axvline(1000, color="red", linestyle="--", label="Contract 1000")
plt.title("acstation1: Upload distribution")
plt.xlabel("Upload (Mbps)")
plt.legend()

plt.tight_layout()
plt.show()
# BETTER OUTLIERS: IQR METHOD (auto-detects low speeds)
Q1_dl = df_acstation["Download_Mbps"].quantile(0.25)
Q3_dl = df_acstation["Download_Mbps"].quantile(0.75)
IQR_dl = Q3_dl - Q1_dl
LOW_DL_CUTOFF = Q1_dl - 1.5 * IQR_dl

Q1_ul = df_acstation["Upload_Mbps"].quantile(0.25)
Q3_ul = df_acstation["Upload_Mbps"].quantile(0.75)
IQR_ul = Q3_ul - Q1_ul
LOW_UL_CUTOFF = Q1_ul - 1.5 * IQR_ul

print(f"Download outliers cutoff: {LOW_DL_CUTOFF:.0f} Mbps (IQR)")
print(f"Upload outliers cutoff: {LOW_UL_CUTOFF:.0f} Mbps (IQR)")

df_acstation["Outlier_Download"] = df_acstation["Download_Mbps"] < LOW_DL_CUTOFF
df_acstation["Outlier_Upload"] = df_acstation["Upload_Mbps"] < LOW_UL_CUTOFF

print(f"Download outliers: {df_acstation['Outlier_Download'].sum()}")
print(f"Upload outliers: {df_acstation['Outlier_Upload'].sum()}")


# CLEAN OUTLIER PLOT
plt.figure(figsize=(14, 5))
sns.lineplot(data=df_acstation, x="Timestamp", y="Download_Mbps", label="Download", color="blue")

outliers = df_acstation[df_acstation["Outlier_Download"]]
plt.scatter(outliers["Timestamp"], outliers["Download_Mbps"], 
            color="red", s=50, label="Statistical outliers", zorder=3)

plt.axhline(1000, color="green", linestyle="--", alpha=0.7, label="Contract 1000 Mbps")
plt.axhline(LOW_DL_CUTOFF, color="orange", linestyle=":", label=f"IQR cutoff {LOW_DL_CUTOFF:.0f}")
plt.title("acstation1: Download with statistical outliers")
plt.xlabel("Time")
plt.ylabel("Download (Mbps)")
plt.legend()
plt.tight_layout()
plt.show()

# BUSINESS SUMMARY
print("\n" + "="*50)
print("ACSTATION1 SUMMARY (hourly office baseline)")
print("="*50)
print(f"Tests: {len(df_acstation)}")
print(f"Avg download: {df_acstation['Download_Mbps'].mean():.0f} Mbps ({100*df_acstation['Download_Mbps'].mean()/1000:.0f}% of contract)")
print(f"Avg upload:   {df_acstation['Upload_Mbps'].mean():.0f} Mbps ({100*df_acstation['Upload_Mbps'].mean()/1000:.0f}% of contract)")
print(f"Tests >900 Mbps: {100*(df_acstation['Download_Mbps']>900).mean():.1f}%")
print(f"Tests >800 Mbps: {100*(df_acstation['Download_Mbps']>800).mean():.1f}%")
print("="*50)


# QUALITY METRICS
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

sns.lineplot(data=df_acstation, x="Timestamp", y="Ping_ms", ax=axes[0,0])
axes[0,0].set_title("Ping (ms)")

sns.lineplot(data=df_acstation, x="Timestamp", y="Jitter_ms", ax=axes[0,1])
axes[0,1].set_title("Jitter (ms)")

sns.lineplot(data=df_acstation, x="Timestamp", y="Packet_Loss", ax=axes[1,0])
axes[1,0].set_title("Packet Loss (%)")

df_acstation.boxplot(column="Download_Mbps", by="Server", ax=axes[1,1])
axes[1,1].set_title("Download by Server")

plt.tight_layout()
plt.show()

# DAILY AVERAGES TABLE
df_acstation["Date"] = df_acstation["Timestamp"].dt.date
daily_avg = df_acstation.groupby("Date")[["Download_Mbps", "Upload_Mbps", "Ping_ms", "Packet_Loss"]].agg(["mean", "count"]).round(1)
print("\nDaily averages:")
print(daily_avg)

# GAP DETECTION (missing hourly tests)
df_acstation["Hour"] = df_acstation["Timestamp"].dt.floor("h")
start_day = df_acstation["Timestamp"].min().floor("D")
end_day = df_acstation["Timestamp"].max().floor("D")
expected_hours = pd.date_range(start=start_day, end=end_day + pd.Timedelta(hours=23), freq="h")
actual_hours = set(df_acstation["Hour"])
missing = expected_hours[~expected_hours.isin(actual_hours)]
print(f"\nMissing hourly tests: {len(missing)} ({missing[:3] if len(missing)>0 else 'none'})")

# SAVE SUMMARY CSV
summary = df_acstation[["Timestamp", "Download_Mbps", "Upload_Mbps", "Ping_ms", "Packet_Loss", "Server"]].copy()
summary.to_csv("acstation1_clean_summary.csv", index=False)
print("Saved clean summary → acstation1_clean_summary.csv")

# SHOW OUTLIER DETAILS
outliers = df_acstation[df_acstation["Outlier_Download"] | df_acstation["Outlier_Upload"]]
print("\nOUTLIER DETAILS:")
print(outliers[["Timestamp", "Download_Mbps", "Upload_Mbps", "Ping_ms", "Packet_Loss", "Server"]].round(1))

# FINAL DASHBOARD PLOT - FIXED WEEKEND SHADING
plt.figure(figsize=(16, 6))

sns.lineplot(data=df_acstation, x="Timestamp", y="Download_Mbps", label="Download", linewidth=2)
sns.lineplot(data=df_acstation, x="Timestamp", y="Upload_Mbps", label="Upload", linewidth=2)

plt.axhline(1000, color="red", linestyle="--", alpha=0.8, label="Contract 1000")

# Shade outliers
outliers_dl = df_acstation[df_acstation["Outlier_Download"]]
plt.scatter(outliers_dl["Timestamp"], outliers_dl["Download_Mbps"], 
            color="red", s=100, marker="x", label=f"Outliers ({len(outliers_dl)})", zorder=5)

# Manual weekend shading (simpler, no 'where' issue)
weekend_mask = df_acstation["Timestamp"].dt.weekday.isin([5,6])
if weekend_mask.any():
    plt.axvspan(df_acstation.loc[weekend_mask, "Timestamp"].min(), 
                df_acstation.loc[weekend_mask, "Timestamp"].max(), 
                alpha=0.2, color="yellow", label="Weekend data")

plt.title("Office Internet: acstation1 Hourly (Cleaned)", fontsize=16, fontweight="bold")
plt.xlabel("Date")
plt.ylabel("Speed (Mbps)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("office_internet_dashboard.png", dpi=300, bbox_inches="tight")
plt.show()

print("Dashboard saved → office_internet_dashboard.png")

# ============================================================
# GENERATE MARKDOWN REPORT
# ============================================================
from datetime import datetime

report_lines = []

# Header
report_lines.append("# Internet Speed Analysis Report")
report_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
report_lines.append(f"**Data Source:** acstation1 (hourly office baseline)\n")

# Overview
report_lines.append("## Overview\n")
report_lines.append(f"| Metric | Value |")
report_lines.append(f"|--------|-------|")
report_lines.append(f"| Total Tests | {len(df_acstation)} |")
report_lines.append(f"| Date Range | {df_acstation['Timestamp'].min().strftime('%Y-%m-%d %H:%M')} to {df_acstation['Timestamp'].max().strftime('%Y-%m-%d %H:%M')} |")
report_lines.append(f"| Missing Hourly Tests | {len(missing)} |")
report_lines.append("")

# Speed Summary
report_lines.append("## Speed Summary\n")
report_lines.append("### Download Speed\n")
report_lines.append(f"| Statistic | Value |")
report_lines.append(f"|-----------|-------|")
dl_stats = df_acstation["Download_Mbps"].describe()
report_lines.append(f"| Mean | {dl_stats['mean']:.1f} Mbps ({100*dl_stats['mean']/1000:.1f}% of contract) |")
report_lines.append(f"| Std Dev | {dl_stats['std']:.1f} Mbps |")
report_lines.append(f"| Min | {dl_stats['min']:.1f} Mbps |")
report_lines.append(f"| 25th Percentile | {dl_stats['25%']:.1f} Mbps |")
report_lines.append(f"| Median | {dl_stats['50%']:.1f} Mbps |")
report_lines.append(f"| 75th Percentile | {dl_stats['75%']:.1f} Mbps |")
report_lines.append(f"| Max | {dl_stats['max']:.1f} Mbps |")
report_lines.append("")

report_lines.append("### Upload Speed\n")
report_lines.append(f"| Statistic | Value |")
report_lines.append(f"|-----------|-------|")
ul_stats = df_acstation["Upload_Mbps"].describe()
report_lines.append(f"| Mean | {ul_stats['mean']:.1f} Mbps ({100*ul_stats['mean']/1000:.1f}% of contract) |")
report_lines.append(f"| Std Dev | {ul_stats['std']:.1f} Mbps |")
report_lines.append(f"| Min | {ul_stats['min']:.1f} Mbps |")
report_lines.append(f"| 25th Percentile | {ul_stats['25%']:.1f} Mbps |")
report_lines.append(f"| Median | {ul_stats['50%']:.1f} Mbps |")
report_lines.append(f"| 75th Percentile | {ul_stats['75%']:.1f} Mbps |")
report_lines.append(f"| Max | {ul_stats['max']:.1f} Mbps |")
report_lines.append("")

# Performance vs Contract
report_lines.append("## Performance vs Contract (1000 Mbps)\n")
report_lines.append(f"| Threshold | Percentage of Tests |")
report_lines.append(f"|-----------|---------------------|")
report_lines.append(f"| >900 Mbps | {100*(df_acstation['Download_Mbps']>900).mean():.1f}% |")
report_lines.append(f"| >800 Mbps | {100*(df_acstation['Download_Mbps']>800).mean():.1f}% |")
report_lines.append(f"| >700 Mbps | {100*(df_acstation['Download_Mbps']>700).mean():.1f}% |")
report_lines.append(f"| >500 Mbps | {100*(df_acstation['Download_Mbps']>500).mean():.1f}% |")
report_lines.append("")

# Quality Metrics
report_lines.append("## Quality Metrics\n")
report_lines.append(f"| Metric | Mean | Min | Max |")
report_lines.append(f"|--------|------|-----|-----|")
report_lines.append(f"| Ping | {df_acstation['Ping_ms'].mean():.1f} ms | {df_acstation['Ping_ms'].min():.1f} ms | {df_acstation['Ping_ms'].max():.1f} ms |")
report_lines.append(f"| Jitter | {df_acstation['Jitter_ms'].mean():.2f} ms | {df_acstation['Jitter_ms'].min():.2f} ms | {df_acstation['Jitter_ms'].max():.2f} ms |")
report_lines.append(f"| Packet Loss | {df_acstation['Packet_Loss'].mean():.2f}% | {df_acstation['Packet_Loss'].min():.2f}% | {df_acstation['Packet_Loss'].max():.2f}% |")
report_lines.append("")

# Outliers Section
report_lines.append("## Outlier Analysis\n")
report_lines.append(f"**IQR-based cutoffs:**")
report_lines.append(f"- Download: {LOW_DL_CUTOFF:.0f} Mbps")
report_lines.append(f"- Upload: {LOW_UL_CUTOFF:.0f} Mbps\n")
report_lines.append(f"**Outliers detected:**")
report_lines.append(f"- Download outliers: {df_acstation['Outlier_Download'].sum()}")
report_lines.append(f"- Upload outliers: {df_acstation['Outlier_Upload'].sum()}\n")

if len(outliers) > 0:
    report_lines.append("### Outlier Details\n")
    report_lines.append("| Timestamp | Download (Mbps) | Upload (Mbps) | Ping (ms) | Packet Loss | Server |")
    report_lines.append("|-----------|-----------------|---------------|-----------|-------------|--------|")
    for _, row in outliers.iterrows():
        report_lines.append(f"| {row['Timestamp'].strftime('%Y-%m-%d %H:%M')} | {row['Download_Mbps']:.1f} | {row['Upload_Mbps']:.1f} | {row['Ping_ms']:.1f} | {row['Packet_Loss']:.2f}% | {row['Server']} |")
    report_lines.append("")

# Daily Averages
report_lines.append("## Daily Averages\n")
report_lines.append("| Date | Download (Mbps) | Upload (Mbps) | Ping (ms) | Packet Loss | Test Count |")
report_lines.append("|------|-----------------|---------------|-----------|-------------|------------|")
daily_simple = df_acstation.groupby("Date").agg({
    "Download_Mbps": "mean",
    "Upload_Mbps": "mean", 
    "Ping_ms": "mean",
    "Packet_Loss": "mean",
    "Timestamp": "count"
}).round(1)
for date, row in daily_simple.iterrows():
    report_lines.append(f"| {date} | {row['Download_Mbps']:.1f} | {row['Upload_Mbps']:.1f} | {row['Ping_ms']:.1f} | {row['Packet_Loss']:.2f}% | {int(row['Timestamp'])} |")
report_lines.append("")

# Save markdown report
report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stats", "speed_report.md")
os.makedirs(os.path.dirname(report_path), exist_ok=True)
with open(report_path, "w") as f:
    f.write("\n".join(report_lines))

print(f"\n Markdown report saved → stats/speed_report.md")