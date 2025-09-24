import cvxpy as cp
import polars as pl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from geopy.distance import geodesic
import mpld3

df = pd.read_csv("data/speeds_2025.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.sort_values(['route_id','timepoint_stop_id','timestamp'])
unique_routes = df['route_id'].unique()


def get_values():

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

    return P_r, s_r0, alpha_r

def calculate():

    # variables
    # passengers per hr, avg speed, congestion coefficients
    P_r, s_r0, alpha_r = get_values()
    # number of routes
    R = len(unique_routes)
    # bus capacity
    C = 50
    # fleet size
    N_r = 1100 * np.ones(R)
    # route length in feet
    L_r = 100000 * np.ones(R)

    s_min = 5 * np.ones(R)  # min speed
    s_max = 35 * np.ones(R) # max speed

    df_routes = pd.DataFrame({'route_id': unique_routes})
    df_routes = df_routes.sort_values(by="route_id")

    fixed_headways = [5] * R
    headways = pd.DataFrame({
        'fixed_headway': fixed_headways
    })

    objects = [df_routes, P_r, s_r0, headways]

    clean_objs = []
    for obj in objects:
        if isinstance(obj, pd.Series):
            clean_objs.append(obj.reset_index(drop=True).to_frame())
        else:
            clean_objs.append(obj.reset_index(drop=True))

    route_params = pd.concat(clean_objs, axis=1, ignore_index=True)
    route_params.columns = ['route', 'P_r', 's_r0', 'headway']

    # head_way
    h_r = route_params['headway'].values

    # optimization
    s = cp.Variable(R)

    objective = cp.Maximize(cp.sum(cp.multiply(P_r,s)) / cp.sum(P_r))

    constraints = [
        s >= s_min,
        s <= L_r / (N_r * h_r),
    ]

    prob = cp.Problem(objective, constraints)
    prob.solve()

    s_opt = np.array(s.value).flatten()

    route_params['optimized_speed'] = s_opt
    route_params['max_speed'] = L_r / (N_r * h_r)
    route_params['is_max_constrained'] = route_params['optimized_speed'] >= route_params['max_speed'] - 1e-5

    max_constrained_routes = route_params[route_params['is_max_constrained']]
    
    routes = route_params['route']
    current = route_params['s_r0']
    optimized = route_params['optimized_speed']
    
    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(routes, current, label='Current Speed', marker='o')
    ax.plot(routes, optimized, label='Optimized Speed', marker='x')
    ax.set_xlabel('Route')
    ax.set_ylabel('Speed (mph)')
    ax.set_title('Current vs Optimized Bus Speeds per Route')
    ax.legend()
    ax.grid(True)
    plt.xticks(rotation=45)
    
    html_str = mpld3.fig_to_html(fig)
    with open("bus_speeds.html", "w") as f:
        f.write(html_str)

    print("Plot saved to bus_speeds.html")

if __name__ == "__main__":
    calculate()