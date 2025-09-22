import pandas as pd
from pathlib import Path

speeds_path = Path("data_work/hunter_speeds_filtered.parquet")
ace_path = Path("data_raw/MTA_Bus_Automated_Camera_Enforced_Routes__Beginning_October_2019_20250921.csv")
output_path = Path("data_work/hunter_speeds_ace_labeled.parquet")

speeds = pd.read_parquet(speeds_path)
ace = pd.read_csv(ace_path)

ace = ace[ace['Program'] == 'ACE']

# change to match column names
ace = ace.rename(columns={
    "Route": "Route ID",
    "Implementation Date": "ace_start_date"
})

ace['ace_start_date'] = pd.to_datetime(ace["ace_start_date"], errors="coerce") # errors avoid crashes

# merge ace dates onto every speed row
df = speeds.merge(ace[["Route ID", "ace_start_date"]], on="Route ID", how='left')
# keep every row from speeds, add ace_start_date when theres a match

# parse timestamps
df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
df['Date'] = df['Timestamp'].dt.date
df['Date'] = pd.to_datetime(df['Date'])

WARNING_DAYS = 60

def label_status(row):
    d = row['Date']
    start = row['ace_start_date']
    if pd.isna(start):
        return "no_ace"
    warn_end = start + pd.Timedelta(days=WARNING_DAYS) - pd.Timedelta(days=1)
    post_begin = start + pd.Timedelta(days=WARNING_DAYS)
    
    if d < start:
        return "pre_ace"
    elif start <= d <= warn_end:
        return "warning"
    else:
        return "post_ace"

df['ace_status'] = df.apply(label_status, axis=1)

df.to_parquet(output_path, index=False)
print(f"[DONE] Saved label speeds -> {output_path} with {len(df):,} rows")

print(df['ace_status'].value_counts())