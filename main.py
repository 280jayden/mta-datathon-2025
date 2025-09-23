import pandas as pd
import numpy as np
import plotly.express as px
import folium
from folium.plugins import HeatMap

# Datathon business questions:

# (1) Which MTA bus routes are highly utilized by CUNY 
# students? For routes that are automated camera-enforced,
# how have bus speeds changed over time?

# (2) Some vehicles stopped in violation are exempt from
#  fines due to business reasons. For vehicles that are 
# exempt, are there repeat offenders? Where are exempt 
# vehicles frequently in violation?

#(3) Some automated camera-enforced routes travel within 
# or cross Manhattan’s Central Business District. 
# How have violations on these routes changed alongside 
# the implementation of congestion pricing?


def get_samples():
    df_violations = pd.read_csv("data/violations.csv")
    df_speeds_2025 = pd.read_csv("data/speeds_2025.csv")
    df_speeds_2023_24 = pd.read_csv("data/speeds_2023-24.csv")

    violations_sample = df_violations.sample(frac=0.01,random_state=42)
    speeds_2025_sample = df_speeds_2025.sample(frac=0.01,random_state=42)
    speeds_2023_24_sample = df_speeds_2023_24.sample(frac=0.01,random_state=42)

    violations_sample.to_csv("data/violations_sample.csv",index=False)
    speeds_2025_sample.to_csv("data/speeds_2025_sample.csv",index=False)
    speeds_2023_24_sample.to_csv("data/speeds_2023_24_sample.csv",index=False)

# separates violation sample into before/after congestion policy
# then plots it
def plot():

    cutoff = pd.Timestamp("2025-01-05 00:00:00")

    df = pd.read_csv("data/violations_sample.csv", parse_dates=["first_occurrence"])

    df['first_occurrence'] = pd.to_datetime(df['first_occurrence'], unit='s', errors='coerce')
    df_before = df[df['first_occurrence'] < cutoff]

    df_after = df[df['first_occurrence'] >= cutoff]

    m = folium.Map(
        location=[df['violation_latitude'].mean(),df['violation_longitude'].mean()],
        zoom_start=12
    )

    l = folium.Map(
        location=[df['violation_latitude'].mean(),df['violation_longitude'].mean()],
        zoom_start=12
    )

    df_before.to_csv("data/violations_before_01052025.csv",index=False)
    df_after.to_csv("data/violations_after_01052025.csv",index=False)

    heat_data_m = df_before[['violation_latitude','violation_longitude']].dropna().values.tolist()
    heat_data_l = df_after[['violation_latitude','violation_longitude']].dropna().values.tolist()


    HeatMap(heat_data_m,radius=8,blue=15).add_to(m)
    HeatMap(heat_data_l,radius=8,blue=15).add_to(l)

    m.save("data/violations__before_heatmap.html")
    l.save("data/violations__after_heatmap.html")


if __name__ == "__main__":
    plot()




