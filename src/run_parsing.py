"""
run_parsing.py

Manual verification script.
Reads 'logs/ontap_ems.log', parses it, and creates features.
"""

from src.parser import LogParser
from src.feature_engine import FeatureEngineer
import pandas as pd

LOG_FILE = "logs/ontap_ems.log"

def main():
    print(f"Reading {LOG_FILE}...")
    
    # 1. Parse
    parser = LogParser()
    logs = list(parser.parse_file(LOG_FILE))
    print(f"Parsed {len(logs)} log lines.")
    
    if not logs:
        print("No logs found. Ensure simulator is running.")
        return

    # 2. Extract Features
    engine = FeatureEngineer()
    engine.ingest_stream(logs)
    
    print("Aggregating into 1-minute windows...")
    features = engine.aggregate_window(freq="1min")
    
    # 3. Display
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print("\n--- Feature DataFrame (Head) ---")
    print(features.head(10))
    print("\n--- Feature Stats ---")
    print(features.describe())

if __name__ == "__main__":
    main()
