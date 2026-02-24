import pandas as pd
import plotly.express as px
import os

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# Point to the new data and charts folders
DATA_DIR = os.path.join(BASE_DIR, "data")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")

# Define the exact file paths
RAW_CSV = os.path.join(DATA_DIR, "office_internet_speeds.csv")
CLEAN_CSV = os.path.join(DATA_DIR, "office_internet_speeds_clean.csv")

# Ensure charts folder exists
os.makedirs(CHARTS_DIR, exist_ok=True)

print("📊 Loading clean data for analysis...")
df = pd.read_csv(CLEAN_CSV)
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

#--------------------------------------------------------------------------------------------
# 2. FILTER DATA (WEEKDAYS ONLY)
df["Hour"] = df["Timestamp"].dt.hour
df["Day_of_Week"] = df["Timestamp"].dt.dayofweek  # Monday=0, Sunday=6

# Completely drop weekends to prevent skewed, low-sample data
weekday_df = df[df["Day_of_Week"] < 5].copy()

# Filter for the 8-16 timeframe (already filtered to just weekdays)
office_df = weekday_df[(weekday_df["Hour"] >= 8) & (weekday_df["Hour"] <= 16)].copy()

#--------------------------------------------------------------------------------------------
# CALCULATE AVERAGES
#--------------------------------------------------------------------------------------------
# 1. 24-Hour Averages
avg_dl_24h = weekday_df["Download_Mbps"].mean()
avg_ul_24h = weekday_df["Upload_Mbps"].mean()

# 2. Office Hours (8-16) Averages
avg_dl_office = office_df["Download_Mbps"].mean()
avg_ul_office = office_df["Upload_Mbps"].mean()

print(f"\n📈 24-Hour Weekday Avg: {avg_dl_24h:.0f} Mbps Down / {avg_ul_24h:.0f} Mbps Up")
print(f"📈 Office Hours (8-16) Avg: {avg_dl_office:.0f} Mbps Down / {avg_ul_office:.0f} Mbps Up")

#--------------------------------------------------------------------------------------------
# CHART 1: 24-HOUR PROFILE (Weekdays Only)
print("\n📉 Generating 24-Hour Profile Chart...")
title_24h = (f"24-Hour Speed Profile (Weekdays Only: Linear Boxplot algorithm 25th and 75th percentiles)<br>"
             f"<sup>Avg Speed: ⬇️ {avg_dl_24h:.0f} Mbps | ⬆️ {avg_ul_24h:.0f} Mbps</sup>")

fig1 = px.box(
    weekday_df, x="Hour", y="Download_Mbps",
    title=title_24h,
    labels={"Hour": "Hour of the Day (0-23)", "Download_Mbps": "Download Speed (Mbps)"},
    color_discrete_sequence=["#636efa"], # Blue
    points="all" 
)
fig1.update_layout(template="plotly_white", xaxis=dict(tickmode='linear', tick0=0, dtick=1))
fig1.write_html(os.path.join(CHARTS_DIR, "hourly_profile_24h.html"))

#--------------------------------------------------------------------------------------------
# CHART 2: 8-16 HOURS PROFILE (Weekdays Only)
print("📉 Generating 8-16 Hours Profile Chart...")
title_office = (f"Office Hours Speed Profile (Weekdays 8-16: Linear Boxplot algorithm 25th and 75th percentiles)<br>"
                f"<sup>Avg Speed: ⬇️ {avg_dl_office:.0f} Mbps | ⬆️ {avg_ul_office:.0f} Mbps</sup>")

fig2 = px.box(
    office_df, x="Hour", y="Download_Mbps",
    title=title_office,
    labels={"Hour": "Hour of the Day (8-16)", "Download_Mbps": "Download Speed (Mbps)"},
    color_discrete_sequence=["#e02d0e"], # Red
    points="all" 
)

# Force the X-axis to only show 8 through 16 sequentially
fig2.update_layout(template="plotly_white", xaxis=dict(tickmode='linear', tick0=8, dtick=1))
fig2.write_html(os.path.join(CHARTS_DIR, "hourly_profile_8_to_16.html"))

#--------------------------------------------------------------------------------------------
print("\n" + "="*50)
print("✅ ANALYSIS COMPLETE! Charts saved in the 'charts' folder:")
print(f"📄 {os.path.abspath(os.path.join(CHARTS_DIR, 'hourly_profile_24h.html'))}")
print(f"📄 {os.path.abspath(os.path.join(CHARTS_DIR, 'hourly_profile_8_to_16.html'))}")
print("="*50)
