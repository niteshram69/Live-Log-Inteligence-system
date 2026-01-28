"""
feature_engine.py

Aggregates parsed log dictionaries into time-series features.
"""

import pandas as pd
import re
from datetime import timedelta

class FeatureEngineer:
    def __init__(self):
        # We will collect logs in a list and then aggregate
        self.buffer = []
        
    def ingest_stream(self, parsed_logs):
        """
        Consumes a generator/list of parsed log dicts.
        """
        for log in parsed_logs:
            self.buffer.append(log)

    def _extract_latency(self, message):
        """
        Extracts latency (ms) from messages like:
        "Workload policy_group_1 latency is 45ms (Threshold: 20ms)."
        """
        match = re.search(r"latency is (\d+)ms", message)
        if match:
            return int(match.group(1))
        return 0

    def aggregate_window(self, freq="1min"):
        """
        Converts buffered logs into a Pandas DataFrame time-series.
        Freq: pandas offset alias (e.g., '1min', '5min', '1H').
        """
        if not self.buffer:
            return pd.DataFrame()

        df = pd.DataFrame(self.buffer)
        
        # Ensure timestamp is index
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        # 1. Base Counts
        # Resample allows us to group by time
        # We want to aggregate multiple metrics
        
        # Create helper columns
        df['is_error'] = df['severity'].apply(lambda s: 1 if s in ['ERROR', 'ALERT', 'EMERGENCY'] else 0)
        df['is_warning'] = df['severity'] == 'WARNING'
        df['is_vol_full'] = df['event'] == 'monitor.volume.nearlyFull'
        df['latency_val'] = df.apply(lambda row: self._extract_latency(row['message']) if row['event'] == 'qos.latency.high' else None, axis=1)

        # Aggregate
        agg_funcs = {
            'event': 'count',           # Total log volume
            'is_error': 'sum',          # Error count
            'is_warning': 'sum',        # Warning count
            'is_vol_full': 'sum',       # Specific pattern count
            'latency_val': 'mean'       # Avg Latency (ignores NaNs)
        }
        
        # Resample
        features = df.resample(freq).agg(agg_funcs)
        
        # Rename columns for clarity
        features.rename(columns={
            'event': 'log_count',
            'is_error': 'error_count',
            'is_warning': 'warning_count',
            'is_vol_full': 'vol_full_events',
            'latency_val': 'avg_latency'
        }, inplace=True)

        # Fill NaNs (e.g., no latency logs in that minute = 0 latency)
        features['avg_latency'] = features['avg_latency'].fillna(0)
        
        # Add Unique Nodes count (requires a lambda)
        unique_nodes = df.resample(freq)['node'].nunique()
        features['unique_nodes'] = unique_nodes

        return features

if __name__ == "__main__":
    # Test stub
    pass
