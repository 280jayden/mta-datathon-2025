import pandas as pd
import requests

def main():
    url = "https://data.ny.gov/api/odata/v4/ki2b-sg5y"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data['value'])
    print((df.head()))

if __name__ == "__main__":
    main()