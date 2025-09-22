import pandas as pd
import requests as rq
import os

def fetch_data():
    url = "https://data.ny.gov/api/odata/v4/ki2b-sg5y"
    all_data = []

    while url:
        response = rq.get(url)
        response.raise_for_status()
        data = response.json()
        all_data.extend(data['value'])
        url = data.get('@odata.nextLink')
    
    df = pd.DataFrame(all_data)

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/data.csv",index=False)

if __name__ == "__main__":
    fetch_data()
