import pandas as pd
import numpy as np

def main():
    df = pd.read_csv("data/data.csv")

    print(df.head())
    print(df.describe())

if __name__ == "__main__":
    main()




