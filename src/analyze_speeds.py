import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np
from datetime import datetime

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

# 2. START FROM Jan 27 (Skipping early MacBook tests)
df_acstation = df_acstation[df_acstation["Timestamp"] >= "2026-01-27 00:00:00"]

# 3. SORT by time
df_acstation = df_acstation.sort_values("Timestamp").reset_index(drop=True)

# Add Hour column early for analysis
df_acstation["Hour"] = df_acstation["Timestamp"].dt.hour
df_acstation["Date_Only"] = df_acstation["Timestamp"].dt.date

print("Total acstation1 rows after filtering:", len(df_acstation))
print("Date range:", df_acstation["Timestamp"].min(), "to", df_acstation["Timestamp"].max())
print("\nDownload summary (acstation1 only):")
print(df_acstation["Download_Mbps"].describe())

# ============================================================
# NEW METRIC: CONGESTION SCORE
# ============================================================
# We define "Night" as 23:00 - 06:00 (Pure hardware potential)
# We define "Work Day" as 08:00 - 17:00 (Load test)
night_mask = (df_acstation['Hour'] < 6) | (df_acstation['Hour'] > 22)
day_mask = (df_acstation['Hour'] >= 8) & (df_acstation['Hour'] <= 17)

night_avg = df_acstation.loc[night_mask, 'Download_Mbps'].mean()
day_avg = df_acstation.loc[day_mask, 'Download_Mbps'].mean()

congestion_score = 0
if night_avg > 0:
    congestion_score = round(((night_avg - day_avg) / night_avg) * 100, 1)

print(f"\n--- CONGESTION ANALYSIS ---")
print(f"Night Avg (Off-Peak): {night_avg:.1f} Mbps")
print(f"Day Avg (Peak Work):  {day_avg:.1f} Mbps")
print(f"CONGESTION SCORE:     {congestion_score}% drop during work hours")
print(f"---------------------------\n")


# 1. TIME SERIES PLOT
plt.figure(figsize=(14, 5))
sns.lineplot(data=df_acstation, x="Timestamp", y="Download_Mbps", label="Download")
sns.lineplot(data=df_acstation, x="Timestamp", y="Upload_Mbps", label="Upload")

plt.axhline(1000, color="red", linestyle="--", label="Contracted 1000 Mbps")
plt.title(f"acstation1: Timeline (Congestion Score: -{congestion_score}%)")
plt.xlabel("Time")
plt.ylabel("Speed (Mbps)")
plt.legend()
plt.tight_layout()
plt.show()

# 2. DISTRIBUTION PLOT
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

# 3. OUTLIER ANALYSIS (IQR METHOD)
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

# 4. OUTLIER PLOT
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

# 5. BUSINESS SUMMARY PRINT
print("\n" + "="*50)
print("ACSTATION1 SUMMARY (hourly office baseline)")
print("="*50)
print(f"Tests: {len(df_acstation)}")
print(f"Avg download: {df_acstation['Download_Mbps'].mean():.0f} Mbps ({100*df_acstation['Download_Mbps'].mean()/1000:.0f}% of contract)")
print(f"Avg upload:   {df_acstation['Upload_Mbps'].mean():.0f} Mbps ({100*df_acstation['Upload_Mbps'].mean()/1000:.0f}% of contract)")
print(f"Tests >900 Mbps: {100*(df_acstation['Download_Mbps']>900).mean():.1f}%")
print(f"Tests >800 Mbps: {100*(df_acstation['Download_Mbps']>800).mean():.1f}%")
print("="*50)


# 6. QUALITY METRICS
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

sns.lineplot(data=df_acstation, x="Timestamp", y="Ping_ms", ax=axes[0,0])
axes[0,0].set_title("Ping (ms)")

sns.lineplot(data=df_acstation, x="Timestamp", y="Jitter_ms", ax=axes[0,1])
axes[0,1].set_title("Jitter (ms)")

# Highlight Packet Loss Threshold
sns.lineplot(data=df_acstation, x="Timestamp", y="Packet_Loss", ax=axes[1,0], color="red")
axes[1,0].axhline(1.0, color="black", linestyle="--", alpha=0.5, label="Bad Quality (>1%)")
axes[1,0].set_title("Packet Loss (%) - CRITICAL METRIC")
axes[1,0].legend()

df_acstation.boxplot(column="Download_Mbps", by="Server", ax=axes[1,1])
axes[1,1].set_title("Download by Server")

plt.tight_layout()
plt.show()

# ============================================================
# NEW VISUALIZATION: THE HEATMAP (The "Smoking Gun")
# ============================================================
# We create a pivot table: Rows = Date, Columns = Hour, Values = Speed
pivot_table = df_acstation.pivot_table(
    index="Date_Only", 
    columns="Hour", 
    values="Download_Mbps", 
    aggfunc="mean"
)

plt.figure(figsize=(12, 6))
sns.heatmap(pivot_table, cmap="RdYlGn", vmin=500, vmax=1000, annot=True, fmt=".0f", cbar_kws={'label': 'Mbps'})
plt.title(f"Network Speed Heatmap (Red = Slow, Green = Fast)\nCongestion Score: {congestion_score}% Drop During Day")
plt.xlabel("Hour of Day")
plt.ylabel("Date")
plt.tight_layout()
plt.show()


# 7. DAILY AVERAGES TABLE
df_acstation["Date"] = df_acstation["Timestamp"].dt.date
daily_avg = df_acstation.groupby("Date")[["Download_Mbps", "Upload_Mbps", "Ping_ms", "Packet_Loss"]].agg(["mean", "count"]).round(1)
print("\nDaily averages:")
print(daily_avg)

# 8. GAP DETECTION
start_day = df_acstation["Timestamp"].min().floor("D")
end_day = df_acstation["Timestamp"].max().floor("D")
expected_hours = pd.date_range(start=start_day, end=end_day + pd.Timedelta(hours=23), freq="h")
actual_hours = set(df_acstation["Timestamp"].dt.floor("h"))
missing = expected_hours[~expected_hours.isin(actual_hours)]
print(f"\nMissing hourly tests: {len(missing)} ({missing[:3] if len(missing)>0 else 'none'})")

# 9. SAVE SUMMARY CSV
summary = df_acstation[["Timestamp", "Download_Mbps", "Upload_Mbps", "Ping_ms", "Packet_Loss", "Server"]].copy()
summary.to_csv("acstation1_clean_summary.csv", index=False)
print("Saved clean summary → acstation1_clean_summary.csv")

# SHOW OUTLIER DETAILS
outliers = df_acstation[df_acstation["Outlier_Download"] | df_acstation["Outlier_Upload"]]
print("\nOUTLIER DETAILS:")
# Use dt.round only if printing purely timestamp, otherwise standard round works for floats
print(outliers[["Timestamp", "Download_Mbps", "Upload_Mbps", "Ping_ms", "Packet_Loss", "Server"]].round(1))

# 10. FINAL DASHBOARD PLOT
plt.figure(figsize=(16, 6))

sns.lineplot(data=df_acstation, x="Timestamp", y="Download_Mbps", label="Download", linewidth=2)
sns.lineplot(data=df_acstation, x="Timestamp", y="Upload_Mbps", label="Upload", linewidth=2)

plt.axhline(1000, color="red", linestyle="--", alpha=0.8, label="Contract 1000")

# Shade outliers
outliers_dl = df_acstation[df_acstation["Outlier_Download"]]
plt.scatter(outliers_dl["Timestamp"], outliers_dl["Download_Mbps"], 
            color="red", s=100, marker="x", label=f"Outliers ({len(outliers_dl)})", zorder=5)

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
# GENERATE MARKDOWN REPORT (WITH NEW CONGESTION DATA)
# ============================================================
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
report_lines.append(f"| Congestion Score | **{congestion_score}%** (Speed drop during business hours) |")
report_lines.append("")

# Speed Summary
report_lines.append("## Speed Summary\n")
report_lines.append("### Download Speed\n")
report_lines.append(f"| Statistic | Value |")
report_lines.append(f"|-----------|-------|")
dl_stats = df_acstation["Download_Mbps"].describe()
report_lines.append(f"| Mean | {dl_stats['mean']:.1f} Mbps ({100*dl_stats['mean']/1000:.1f}% of contract) |")
report_lines.append(f"| Median | {dl_stats['50%']:.1f} Mbps |")
report_lines.append(f"| Max | {dl_stats['max']:.1f} Mbps |")
report_lines.append("")

# Quality Metrics
report_lines.append("## Quality Metrics (Packet Loss is Critical)\n")
report_lines.append(f"| Metric | Mean | Max | Status |")
report_lines.append(f"|--------|------|-----|--------|")
pl_status = "**CRITICAL**" if df_acstation['Packet_Loss'].mean() > 1.0 else "Good"
report_lines.append(f"| Packet Loss | **{df_acstation['Packet_Loss'].mean():.2f}%** | {df_acstation['Packet_Loss'].max():.2f}% | {pl_status} |")
report_lines.append(f"| Ping | {df_acstation['Ping_ms'].mean():.1f} ms | {df_acstation['Ping_ms'].max():.1f} ms | OK |")
report_lines.append("")

# Outliers Section
report_lines.append("## Outlier Analysis\n")
report_lines.append(f"**Congestion & Outliers:**")
report_lines.append(f"- Night Average (00:00-06:00): {night_avg:.0f} Mbps")
report_lines.append(f"- Day Average (08:00-17:00): {day_avg:.0f} Mbps")
report_lines.append(f"- Download outliers detected: {df_acstation['Outlier_Download'].sum()}\n")

if len(outliers) > 0:
    report_lines.append("### Significant Drop-offs\n")
    report_lines.append("| Timestamp | Download | Packet Loss | Server |")
    report_lines.append("|-----------|----------|-------------|--------|")
    for _, row in outliers.iterrows():
        report_lines.append(f"| {row['Timestamp'].strftime('%Y-%m-%d %H:%M')} | {row['Download_Mbps']:.0f} Mbps | {row['Packet_Loss']:.2f}% | {row['Server']} |")
    report_lines.append("")

# Save markdown report
report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stats", "speed_report.md")
os.makedirs(os.path.dirname(report_path), exist_ok=True)
with open(report_path, "w") as f:
    f.write("\n".join(report_lines))

print(f"\nMarkdown report saved → stats/speed_report.md")