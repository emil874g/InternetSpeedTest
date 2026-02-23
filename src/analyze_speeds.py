import pandas as pd
import plotly.express as px
import os

CLEAN_CSV = "office_internet_speeds_clean.csv"
CHARTS_DIR = "charts"

# 1. Create the charts folder if it doesn't exist
os.makedirs(CHARTS_DIR, exist_ok=True)

print("📊 Loading clean data for analysis...")
df = pd.read_csv(CLEAN_CSV)
df["Timestamp"] = pd.to_datetime(df["Timestamp"])
df = df.sort_values("Timestamp") # Ensure chronological order for line charts

# ==========================================
# 3. CALCULATE OVERALL MEANS
# ==========================================
mean_dl = df["Download_Mbps"].mean()
mean_ul = df["Upload_Mbps"].mean()

print("\n" + "="*50)
print("📈 OVERALL AVERAGE SPEEDS:")
print(f"   ⬇️ Download: {mean_dl:.2f} Mbps")
print(f"   ⬆️ Upload:   {mean_ul:.2f} Mbps")
print("="*50 + "\n")

# ==========================================
# BUSINESS LOGIC (Office vs Off-Hours)
# ==========================================
df["Hour"] = df["Timestamp"].dt.hour
df["Day_of_Week"] = df["Timestamp"].dt.dayofweek  # Monday=0, Sunday=6

office_mask = (df["Day_of_Week"] < 5) & (df["Hour"] >= 8) & (df["Hour"] <= 16)

df["Time_Period"] = "Off-Hours (Quiet)"
df.loc[office_mask, "Time_Period"] = "Office Hours (Busy)"

# ==========================================
# CHART 1: TIMELINE SCATTER PLOT
# ==========================================
print("📈 Generating Timeline Scatter Chart...")
fig1 = px.scatter(
    df, x="Timestamp", y="Download_Mbps", color="Time_Period",
    hover_data=["Upload_Mbps", "Ping_ms"],
    title="Internet Download Speeds: Office Load vs. Off-Hours",
    labels={"Download_Mbps": "Download Speed (Mbps)", "Timestamp": "Date / Time"},
    color_discrete_map={"Office Hours (Busy)": "#ef553b", "Off-Hours (Quiet)": "#00cc96"},
    opacity=0.75
)
fig1.add_hline(y=800, line_dash="dot", line_color="black", annotation_text="Expected Speed (~800 Mbps)")
fig1.update_layout(template="plotly_white", hovermode="x unified")
fig1.write_html(os.path.join(CHARTS_DIR, "timeline_scatter.html"))

# ==========================================
# CHART 2: HOURLY PERFORMANCE PROFILE (Box Plot)
# ==========================================
print("📉 Generating Hourly Profile Chart...")
fig2 = px.box(
    df, x="Hour", y="Download_Mbps",
    title="Hourly Speed Profile: Does the office kill the internet?",
    labels={"Hour": "Hour of the Day (0-23)", "Download_Mbps": "Download Speed (Mbps)"},
    color_discrete_sequence=["#636efa"],
    points="all" 
)
fig2.update_layout(template="plotly_white", xaxis=dict(tickmode='linear', tick0=0, dtick=1))
fig2.write_html(os.path.join(CHARTS_DIR, "hourly_profile.html"))

# ==========================================
# 2. CHART 3: CONTINUOUS LINE CHART (DL & UL)
# ==========================================
print("〰️ Generating Continuous Line Chart...")
# We use both DL and UL here so you can see if they drop together
fig3 = px.line(
    df, x="Timestamp", y=["Download_Mbps", "Upload_Mbps"],
    title="Continuous Speed Distribution (Download & Upload)",
    labels={"value": "Speed (Mbps)", "Timestamp": "Date / Time", "variable": "Metric"},
    markers=True # Adds little dots on the line
)
fig3.update_layout(template="plotly_white", hovermode="x unified")
fig3.write_html(os.path.join(CHARTS_DIR, "line_distribution.html"))

print("\n" + "="*50)
print("✅ ANALYSIS COMPLETE! Charts saved in the 'charts' folder:")
print(f"📄 {os.path.abspath(os.path.join(CHARTS_DIR, 'timeline_scatter.html'))}")
print(f"📄 {os.path.abspath(os.path.join(CHARTS_DIR, 'hourly_profile.html'))}")
print(f"📄 {os.path.abspath(os.path.join(CHARTS_DIR, 'line_distribution.html'))}")
print("="*50)
