import pandas as pd
from pandas import DataFrame
from parides.prom_conv import from_prom_to_df
import datetime as dt
import yaml
import sys
import argparse

from kubernetes import client, config
from typing import Any, cast
import json

# Experiment info loader function
#   chaos_type: type of chaosexperiment
#           ns: namespace chaos is located in
def load_experiments_by_type(chaos_type, ns):
    experiment_list = []
    try:
        # chaosexperiment objektumok lekerdezese
        response = client.CustomObjectsApi().list_namespaced_custom_object(
        group="chaos-mesh.org",
        version="v1alpha1",
        namespace=ns,
        plural=chaos_type
        )

        response = cast(dict[str, Any], response)
        # egyes chaosexperimentek kezelese
        for item in response.get("items", []):

            name = item["metadata"]["name"]
            kind = item["kind"]
            spec = item.get("spec")
        
            # idobelyegek kinyerese
            container_records = item.get("status", {}).get("experiment", {}).get("containerRecords", [])

            start_time = ""
            end_time = ""

            if container_records:
                inner_events = container_records[0].get("events", [])
                
                for event in inner_events:
                    if event.get("operation") == "Apply":
                        start_time = event.get("timestamp", "")
                    if event.get("operation") == "Recover":
                        end_time = event.get("timestamp", "")

            experiment_list.append({
                "name": name,
                "kind": kind,
                "spec": spec,
                "start_time": pd.to_datetime(start_time),
                "end_time": pd.to_datetime(end_time),
            })

    except client.ApiException as e:
        print(f"Error checking {chaos_type}: {e}")
    return experiment_list

config.load_kube_config()
#
#---------------------------------------------------------------------
#                        CLI args handling
#---------------------------------------------------------------------
#
parser = argparse.ArgumentParser(description="Faas Data query")
parser.add_argument(
    "--output", 
    type=str, 
    default=None, 
    help="Name of measurement output file"
)
parser.add_argument(
    "-t", 
    type=int, 
    default=10, 
    help="Lenght of measurement in minutes. Measurement timerange: (arg minutes ago, now) default = 10"
)
parser.add_argument(
    "--query", 
    type=str,  
    help="File containing PromQL queries"
)
parser.add_argument(
    "--endpoint", 
    type=str, 
    default="localhost:9090", 
    help="Prometheus endpoint IP:port"
)
args = parser.parse_args()

# Time window
measure_end = dt.datetime.now(dt.timezone.utc)
measure_start = measure_end - dt.timedelta(minutes=args.t)

# Endpoint
endpoint_url = "http://" + args.endpoint

# Query
query_dict = {}
if args.query:
    try:
        with open(args.query, "r") as queryfile:
            query_dict = yaml.safe_load(queryfile)
            print(f"Loaded {len(query_dict)} queries from {args.query}" )
    except FileNotFoundError:
        sys.exit("### ERROR ### - Query file not found. Exiting.")
else:
    sys.exit("No query file specified. Use --query flag!")

print("Hello Beautiful FaaS DATA")

#
#---------------------------------------------------------------------
#              Extracting FaaS data from Prometheus
#---------------------------------------------------------------------
#
dfs = []
for metric_name, query in query_dict.items():
    temp_df = from_prom_to_df(
        url=endpoint_url,
        metrics_query=query,
        start_time=measure_start,
        end_time=measure_end,
        resolution="1s"
    )

    if temp_df.empty:
        print('No data for query: ' + query)
        continue

    # id column eldobasa
    data_col = [c for c in temp_df.columns if c != 'id'][0]
    temp_df = temp_df[data_col]
    temp_df.name = metric_name
    dfs.append(temp_df)


#Merge (timestamp az index)
df = pd.concat(dfs, axis=1)

if df.empty:
    sys.exit('No Data found :,(')

#
#---------------------------------------------------------------------
#               Data labeling with ChaosExperiment type
#---------------------------------------------------------------------
#

# ChaosExperiment types
chaos_types = [
    "networkchaos", "podchaos", "httpchaos", "iochaos", 
    "stresschaos" #, "dnschaos", "timechaos", "kernelchaos"
]
# looping through chaos_types
df_start_time = df.index.min()
df_end_time = df.index.max()

chaos_list = []
for chaos_type in chaos_types:
    part_chaos_list = load_experiments_by_type(chaos_type=chaos_type, ns='chaos-mesh')

    for chaos in part_chaos_list:
        chaos_start_time = chaos["start_time"]
        chaos_end_time = chaos["end_time"]
                                                                                    # Dont include chaos if outside measurement time window
        if(not(df_start_time > chaos_end_time or df_end_time < chaos_start_time)):      #    cend | measurement frame | cstart
            chaos_list.append(chaos) 
                                                           # time   --------------------------------->
# Adding 
df["chaos"] = "Normal"
for chaos in chaos_list:
    c_start = chaos["start_time"]
    c_end = chaos["end_time"]
    c_name = chaos["name"]

    # 3. Create a boolean mask for rows that fall inside this specific chaos window
    # Because df.index is a DatetimeIndex, we can compare it directly to timestamps
    is_during_chaos = (df.index >= c_start) & (df.index <= c_end)

    # 4. Map the chaos name to the rows that match the mask
    df.loc[is_during_chaos, "chaos"] = c_name

        

print('---------------------------------------INFO---------------------------------------')
print(df.info())
print('---------------------------------------------HEAD--------------------------------------')
print(df.head(3))
print('---------------------------------------DESCRIBE----------------------------------------')
print(f"Chaos experiments present: {df["chaos"].unique()} ")
print()
print(df.describe())

if args.output:
    #TODO kell egy kis input validation
    print(f"Measurement result saved to {args.output}")
    df.to_parquet(args.output)