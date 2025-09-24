import polars as pl
import pandas as pd

# load dataset
df = pl.read_csv("data/speeds_2025.csv")

# convert to datetime
df = df.with_columns([
    pl.col('timestamp').str.strptime(pl.Datetime, format=None, strict=False)
])

# calculate end time by adding avg travel time to timestamp(start time)
# timestamp = the time the bus arrives at stop A
# end_time = the time the bus arrives at stop B
# each row in speeds_2025.csv contains data about a bus going from stop A to stop B
df = df.with_columns([
    (pl.col('timestamp') + (pl.col('average_travel_time')*60_000_000).cast(pl.Duration('us'))).alias('end_time')
])

# make start_events
start_events = df.select([
    pl.col("route_id"),
    pl.col("timestamp").alias("time"),
    pl.lit(1).alias("change")
])

# make end_events
end_events = df.select([
    pl.col("route_id"),
    pl.col("end_time").alias("time"),
    pl.lit(-1).alias("change")
])

# concatenate start and end events
events_df = pl.concat([start_events, end_events])

# sort by route and time
events_df = events_df.sort(["route_id", "time"])

# find cumulative active buses per route
events_df = events_df.with_columns([
    pl.col("change").cum_sum().over("route_id").alias("active_buses")
])

# find max active buses per route
fleet_per_route_df = events_df.group_by("route_id").agg([
    pl.max("active_buses").alias("fleet_size")
])

fleet_per_route = dict(zip(fleet_per_route_df["route_id"], fleet_per_route_df["fleet_size"]))
total_fleet_size = sum(fleet_per_route.values())

print(fleet_per_route)
print("Total active fleet size: ", total_fleet_size)

# This estimation is a lower bound for the active fleet
# where active fleet is defined as the number of MTA buses
# counted in this speeds_2025 dataset that is going from 
# stop A to stop B. This calculation is a lower bound because
# it excludes the buses that may continue from stop B to stop C.
# It also is unable to identify which buses are which due to the
# lack of a bus ID column.

# The output of total_fleet_size and fleet_per_route is the 
# number of active buses, respectively, over the period since 
# this dataset's creation, 11/21/24. Thus, on average, 
# There would be about fleet_per_route / 300 and 
# total_fleet_size / 300 respective active fleet counts per day since
# 11/21/24.
# The lower bound for the active fleet size is about 
# 320,000 buses / 300 days = ~1100 active buses per day. 
# According to the MTA webpage, their active fleet is 5700 buses,
# which makes sense with our number considering they would include
# extra buses for maintenance and repair purposes while our estimate
# is a lower bound due to the nature of the calculation.
# This calculation reflects the potential for optimization 
# of reducing buses that aren't in use while maintaining the same
# level of service in bus operations.