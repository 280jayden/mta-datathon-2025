import pandas as pd
import requests
import os
import time

DATASETS = {
    "violations": "https://data.ny.gov/api/odata/v4/kh8p-hcbm",
    "speeds_2025": "https://data.ny.gov/api/odata/v4/kufs-yh3x",
    "speeds_2023-24": "https://data.ny.gov/api/odata/v4/58t6-89vi"

}

def fetch_by_chunk(name,url,chunk_size=1000):
    os.makedirs("data",exist_ok=True)
    all_rows=0
    skip=0
    first_chunk = True
    all_data=[]

    while url:
        batch_url=f"{url}?$top={chunk_size}&$skip={skip}"
        for _ in range(3):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                break
            except:
                time.sleep(0.2)

        rows = data.get("value",[])
        if not rows:
            break

        if url is None and len(rows) == chunk_size:
            url = batch_url

        time.sleep(0.1)

        df = pd.DataFrame(rows)
        url = data.get('@odata.nextLink')

        output_file=f"data/{name}.csv"

        df.to_csv(output_file, mode='a', header=not os.path.exists(output_file), index=False)
        all_rows += len(df)
        print(f"Fetched {len(df)} rows, total so far: {all_rows}")

        skip+=1000
    
    print(f"Finished fetching {all_rows} rows.")

def main():
    for name,url in DATASETS.items():
        fetch_by_chunk(name,url)

if __name__ == "__main__":
    main()
