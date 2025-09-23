import pandas as pd
from pathlib import Path

ROUTES = ["M101", "M102", "M103", "M2", "M3", "M4", "M15+", "M15", "M60+", "M100"]

INPUT_CSV = Path("data_raw/MTA_Bus_Automated_Camera_Enforcement_Violations__Beginning_October_2019_20250919.csv")
OUT_PATH = Path("data_work/violations_routes_filtered.parquet")

CHUNK = 200_000

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

dfs = []
total_in = 0
total_kept = 0


print("[INFO] Processing Chunks...")
for chunk in pd.read_csv(INPUT_CSV, chunksize=CHUNK, low_memory=False):
    total_in += len(chunk)
    # keep only our routes
    mask = chunk["Bus Route ID"].isin(ROUTES)
    part = chunk.loc[mask].copy()
    kept = len(part)
    total_kept += kept
    if kept:
        dfs.append(part)

if not dfs:
    # error handling
    raise SystemExit(f"[STOP] No rows kept. Check the ROUTES list or 'Bus Route ID' column name.")

df = pd.concat(dfs, ignore_index=True)

# add useful columns
df["Datetime"] = pd.to_datetime(df["First Occurrence"], errors='coerce')
df['is_exempt'] = df["Violation Status"].astype(str).str.contains("EXEMPT", case=False, na=False)

# Write new parquet
df.to_parquet(OUT_PATH, index=False)

# logs
print(f"[DONE] Read {total_in:,} rows; kept {total_kept:,} for routes {ROUTES}")
print(f"[WRITE] {OUT_PATH} (rows: {len(df):,})")

# Quick sanity peeks
print("\n[Route counts]")
print(df["Bus Route ID"].value_counts())

print("\n[Exempt flag]")
print(df["is_exempt"].value_counts(dropna=False))