import pandas as pd
import numpy as np
import plotly.express as px
import folium
from folium.plugins import HeatMap
from scipy.stats import ttest_ind

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

# does a spatial analysis on before/after congestion pricing
def analyze():
    df_before = pd.read_csv("data/violations_before_01052025.csv")
    df_after = pd.read_csv("data/violations_after_01052025.csv")
    
    # round to ~1km grid
    df_before['lat_grid'] = df_before['violation_latitude'].round(3)
    df_before['lon_grid'] = df_before['violation_longitude'].round(3)

    df_after['lat_grid'] = df_after['violation_latitude'].round(3)
    df_after['lon_grid'] = df_after['violation_longitude'].round(3)

    grid_before = df_before.groupby(['lat_grid', 'lon_grid']).size().reset_index(name='violations')
    grid_after = df_after.groupby(['lat_grid', 'lon_grid']).size().reset_index(name='violations')

    grid_comparison = pd.merge(grid_before, grid_after, on=['lat_grid','lon_grid'], how='outer', suffixes=('_before','_after')).fillna(0)

    grid_comparison['diff'] = grid_comparison['violations_after'] - grid_comparison['violations_before']

    # Top 10 hotspot changes in before/after
    top_increase = grid_comparison.sort_values('diff', ascending=True).head(10)
    print(top_increase)

# plots the repeat exempt violation offenders' locations
def plot_q2():
    df_before = pd.read_csv("data/violations_before_01052025.csv")
    df_after = pd.read_csv("data/violations_after_01052025.csv")

    df_before['violation_status'] = df_before['violation_status'].str.upper()
    df_after['violation_status'] = df_after['violation_status'].str.upper()

    exempt_before = df_before[df_before['violation_status'].str.contains("EXEMPT")]
    exempt_after = df_after[df_after['violation_status'].str.contains("EXEMPT")]

    exempt_before['is_repeat_offender'] = exempt_before['first_occurrence'] != exempt_before['last_occurrence']
    exempt_after['is_repeat_offender'] = exempt_after['first_occurrence'] != exempt_after['last_occurrence']

    # repeat exempt violators before congestion pricing
    df_repeat_exempt_before = exempt_before[exempt_before['is_repeat_offender']]
    # repeat exempt violators after congestion pricing
    df_repeat_exempt_after = exempt_after[exempt_after['is_repeat_offender']]

    center = [df_before['violation_latitude'].mean(), df_before['violation_longitude'].mean()]

    # heatmap before cutoff
    m_before = folium.Map(location=center, zoom_start=12)
    HeatMap(df_repeat_exempt_before[['violation_latitude','violation_longitude']].values.tolist(), radius=8, blur=15).add_to(m_before)
    m_before.save("data/repeat_heatmap_before.html")

    # heatmap after cutoff
    m_after = folium.Map(location=center, zoom_start=12)
    HeatMap(df_repeat_exempt_after[['violation_latitude','violation_longitude']].values.tolist(), radius=8, blur=15).add_to(m_after)
    m_after.save("data/repeat_heatmap_after.html")

def DiD():
    df = pd.read_csv("data/violations_sample.csv")
    bus_routes = pd.read_csv("data/data.csv")

    # converts bus route - implementation date dataframe to a dictionary
    bus_implementation = bus_routes.set_index('route')['implementation_date'].to_dict()

    # converts to datetime
    df['first_occurrence'] = pd.to_datetime(df['first_occurrence'])
    bus_implementation = {k: pd.to_datetime(v) for k, v in bus_implementation.items()}


    df['timeframe'] = df.apply(
        lambda row: 'before' if row['first_occurrence'] < bus_implementation.get(row['bus_route_id'], pd.Timestamp.max) else 'after',
        axis=1
    )

    # treated = has camera enforcement on route
    df['treated'] = df['bus_route_id'].isin(bus_implementation.keys())

    cutoff = pd.Timestamp("2025-01-05 00:00:00")

    # cbd = congestion pricing policy
    df['is_after'] = df['first_occurrence'] >= cutoff
    df['is_after'] = df['first_occurrence'] >= cutoff

    treated_before = df[(df['treated']) & (~df['is_after'])]
    treated_after  = df[(df['treated']) & (df['is_after'])]

    control_before = df[(~df['treated']) & (~df['is_after'])]
    control_after  = df[(~df['treated']) & (df['is_after'])]

    tb_daily = treated_before.groupby(treated_before['first_occurrence'].dt.date).size()
    ta_daily = treated_after.groupby(treated_after['first_occurrence'].dt.date).size()
    cb_daily = control_before.groupby(control_before['first_occurrence'].dt.date).size()
    ca_daily = control_after.groupby(control_after['first_occurrence'].dt.date).size()

    # Means
    tb_mean = tb_daily.mean()
    ta_mean = ta_daily.mean()
    cb_mean = cb_daily.mean()
    ca_mean = ca_daily.mean()

    treated_change = ta_daily.values - tb_daily.values[:len(ta_daily)]  # align lengths if needed
    control_change = ca_daily.values - cb_daily.values[:len(ca_daily)]

    DiD = (ta_mean - tb_mean) - (ca_mean - cb_mean)

    print("DiD estimate (effect of cameras):", DiD)
    t_stat, p_value = ttest_ind(treated_change, control_change, equal_var=False)
    print("T-statistic:", t_stat)
    print("P-value:", p_value)

    # This DiD and T-test reported an increase of 60 violations on
    # average per day when going from before the congestion policy enforcement
    # This was calculated at a p-value = 1e-114 << 0.05, so this is statistically
    # significant to conclude that there was an increase in violations
    # after the ACE camera enforcement. Maybe just due to the increase
    # cameras, more violations were reported, which means there would be
    # survivorship bias.

if __name__ == "__main__":
    DiD()
