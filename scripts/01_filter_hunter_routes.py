import pandas as pd
from pathlib import Path

# relevant routes
ROUTES = ["M101", "M102", "M103", "M2", "M3", "M4", "M15+"]


# raw data files
INPUT_FILES = [
    "data_raw/MTA_Bus_Route_Segment_Speeds__2023_-_2024_20250921.csv",
    "data_raw/MTA_Bus_Route_Segment_Speeds__Beginning_2025_20250919.csv"
]

# create output path
OUT_PATH = Path("data_work/hunter_speeds_filtered.parquet")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True) # check if parent folder exists

dfs = []

for file in INPUT_FILES:
    print(f"[INFO] Processing {file}")
    for chunk in pd.read_csv(file, chunksize=100000):
        # filter rows for Hunter routes
        chunk_filtered = chunk[chunk['Route ID'].isin(ROUTES)]
        if not chunk_filtered.empty:
            dfs.append(chunk_filtered)

# combine everything
hunter_speeds = pd.concat(dfs, ignore_index=True)

# save to CSV
hunter_speeds.to_parquet(OUT_PATH, index=False)
print(f"[DONE] Wrote {len(hunter_speeds):,} rows -> {OUT_PATH}")

# sanity check
print(hunter_speeds['Route ID'].value_counts())