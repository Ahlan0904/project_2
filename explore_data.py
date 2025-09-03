import pandas as pd
import sys

sys.stdout = open('data_info.txt', 'w', encoding='utf-8')

try:
    df = pd.read_excel('review_crawling_raw.xlsx')
    print("### First 5 rows:")
    print(df.head())
    print("\n### Columns:")
    print(df.columns)
    print("\n### Info:")
    df.info()
except FileNotFoundError:
    print("Error: review_crawling_raw.xlsx not found.")
except Exception as e:
    print(f"An error occurred: {e}")