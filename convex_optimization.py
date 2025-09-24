import cvxpy as py
import polars as pl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from geopy.distance import geodesic

df = pd.read_csv("data/speeds_2025.csv")

df['timestamp'] = pd.to_datetime(df['timestamp'])

df.sort_values(['route_id','timepoint_stop_id','timestamp'])

# dwell_time: time spent at a stop
# use dwell_time as a proxy for passenger capacity
df['dwell_time'] = df.groupby(['route_id', 'timepoint_stop_id'])['timestamp'].diff().dt.total_seconds()
df['dwell_time'] = df['dwell_time'].fillna(0)
avg_dwell_per_route = df.groupby('route_id')['dwell_time'].mean()

# passengers per hr
# this is passengers per hr per route over the sum of the speed_2025.csv dataset
# e.g. B1 route: 1.453489e_+5
# 14000 / 300 = ~46 passengers per hr in one day over the entire B1 fleet
P_r = (avg_dwell_per_route / 3) * 60 # 3 sec per passenger to board, passengers per hour

# free flow speed per route
# This ignores high congestion data and outliers, so we take the 95th percentile
s_r0 = df.groupby('route_id')['average_road_speed'].quantile(0.95) # 95th percentile to ignore outliers

# headway: time diff between consecutive buses
df_first_stop = df[df['timepoint_stop_id'] == df['timepoint_stop_id'].min()]  # first stop
df_first_stop = df_first_stop.sort_values(['route_id', 'timestamp'])
df_first_stop['headway'] = df_first_stop.groupby('route_id')['timestamp'].diff().dt.seconds / 60  # minutes

# alpha_r: congestion coefficient per bus route
# e.g. Q109: np.float(1.0)
alpha_r = {}

def congestion_model(h, alpha):
    return s0_r - alpha / h

for route in df['route_id'].unique():
    route_data = df_first_stop[df_first_stop['route_id'] == route]
    h_values = route_data['headway'].dropna().values
    s_values = route_data['average_road_speed'].dropna().values
    mask_h = h_values > 0
    mask_s = s_values > 0
    h_values = h_values[mask_h]
    s_values = s_values[mask_s]
    s0_r = s_r0[route]
    if len(h_values) > 2:
        popt, _ = curve_fit(lambda h, alpha: s0_r, h_values, s_values, bounds=(0, np.inf))
        alpha_r[route] = popt[0]
    else:
        alpha_r[route] = np.nan

print("Passengers per hour P_r:\n", P_r)
print("Free-flow speed s_r0:\n", s_r0)
print("Congestion coefficients alpha_r:\n", alpha_r)
