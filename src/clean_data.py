import os
import re
import numpy as np
import pandas as pd


RAW_CSV = "office_internet_speeds.csv"
CLEAN_CSV = "office_internet_speeds_clean.csv"


def parse_maybe_locale_number(x):
    if pd.isna(x): return np.nan
    s = str(x).strip()
    if not s or s.lower() in {"nan", "none", "null"}: return np.nan
    
    # Strip letters/spaces
    s = re.sub(r"[^0-9,.\-]", "", s)
    if s in {"", "-", ".", ",", "-.", "-,"}: return np.nan

    # Fix the corrupted .00 bug
    if s.endswith(".00") or s.endswith(",00"): s = s[:-3]
    elif s.endswith(".0") or s.endswith(",0"): s = s[:-2]

    # Fix European decimals
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."): s = s.replace(".", "").replace(",", ".")
        else: s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")

    try: return float(s)
    except ValueError: return np.nan


print("🚀 Running final data cleaning pipeline...\n")


# 1. Load Data as strings
df = pd.read_csv(RAW_CSV, dtype=str, keep_default_na=False)
df.columns = df.columns.str.strip()
print(f"📥 Loaded {len(df)} total raw rows (including MacBooks).")


# 2. STRICTLY filter out MacBooks (keep only acstation1)
df = df[df["Device"].astype(str).str.contains("acstation1", case=False, na=False)].copy()
print(f"💻 Filtered to strictly 'acstation1': {len(df)} rows.")


# 3. Parse Timestamp
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
df = df.dropna(subset=["Timestamp"]).copy()


# 4. Remove Buggy Bursts (Minutes with 3+ simultaneous tests)
df["Minute_Bin"] = df["Timestamp"].dt.floor("min")
minute_counts = df["Minute_Bin"].value_counts()
df["Tests_This_Minute"] = df["Minute_Bin"].map(minute_counts).astype("int64")

df = df[df["Tests_This_Minute"] < 3].copy()
print(f"⏱️  After removing bugged bursts (3+ tests/min): {len(df)} rows.")


# 5. Safe Number Parsing (Fixing the .00 corruption)
num_cols = ["Download_Mbps", "Upload_Mbps", "Ping_ms", "Jitter_ms", "Packet_Loss"]
for col in num_cols:
    if col in df.columns:
        df[col] = df[col].apply(parse_maybe_locale_number)


# 6. Final Clean & Speed Limit Filter (Killing the remaining stragglers)
df = df.dropna(subset=["Download_Mbps", "Upload_Mbps"]).copy()

# Increased the threshold from 100 Mbps to 350 Mbps.
# This cuts off the incredibly low upload stragglers and the remaining downward spikes
# from Jan 30 onwards without touching your legitimate 400+ Mbps data.
df = df[(df["Download_Mbps"] >= 350) & (df["Upload_Mbps"] >= 350)].copy()
print(f"✂️  After stripping low DL/UL stragglers (< 350 Mbps): {len(df)} rows.")


# 7. Save to CSV
df = df.drop(columns=["Minute_Bin", "Tests_This_Minute"]).sort_values("Timestamp").reset_index(drop=True)
output_path = os.path.abspath(CLEAN_CSV)
df.to_csv(output_path, index=False)


print("\n" + "="*50)
print(f"🎉 FINAL CLEAN DATASET: {len(df)} PERFECT ROWS")
print(f"📁 Saved to: {output_path}")
print("="*50)
