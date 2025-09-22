import pandas as pd
import numpy as np
from sodapy import Socrata

client = Socrata("data.ny.gov", None)

results = client.get("khy8p-hchm", limit=2000)

results_df = pd.DataFrame.from_records(results)

