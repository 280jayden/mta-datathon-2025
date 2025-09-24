import cvxpy as py
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from geopy.distance import geodesic

df = pl.read_csv("data/speeds_2025.csv")

df.sort(['timestamp'])

# dwell_time: time spent at a stop
# use dwell_time as a proxy for passenger capacity
df['dwell_time'] = df.groupby(['route_id','timestamp_stop_id'])['timestamp'].diff().dt.seconds.fillna(0)
avg_dwell_per_route = df.groupby('route_id')['dwell_time'].mean()

# passengers per hr
P_r = (avg_dwell_per_route / 3) * 60 # 3 sec per passenger to board, passengers per hour

# free flow speed per route
s_r0 = df.groupby('route_id')['speed'].quantile(0.95) # 95th percentile to ignore outliers

# headway: time diff between consecutive buses
df_first_stop = df[df['stop_id'] == df['stop_id'].min()]  # first stop
df_first_stop = df_first_stop.sort_values(['route_id', 'timestamp'])
df_first_stop['headway'] = df_first_stop.groupby('route_id')['timestamp'].diff().dt.seconds / 60  # minutes

alpha_r = {}

def congestion_model(h, alpha):
    return s_r0 - alpha / h

for route in df['route_id'].unique():
    route_data = df_first_stop[df_first_stop['route_id'] == route]
    h_values = route_data['headway'].dropna().h_values
    s_values = route_data['speed'].dropna().h_values
    s_r0 = s_r0[route]
    if len(h_values) > 2:
        popt, _ = curve_fit(lambda h, alpha: s_r0 - alpha / h, h_values, s_values, bounds=(0, np.inf))
        alpha_r[route] = popt[0]
    else:
        alpha_r[route] = np.nan

print("Passengers per hour P_r:\n", P_r)
print("Free-flow speed s_r0:\n", s_r0)
print("Congestion coefficients alpha_r:\n", alpha_r)
