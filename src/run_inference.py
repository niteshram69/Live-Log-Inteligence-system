"""
run_inference.py

Reads live logs, aggregates them into short windows (e.g., 10s),
and predicts anomalies using the trained model.
"""

import time
import pandas as pd
import os
from src.parser import LogParser
from src.feature_engine import FeatureEngineer
from src.anomaly_detector import OntapAnomalyDetector

MODEL_PATH = "models/iso_forest.pkl"
LOG_FILE = "logs/ontap_ems.log"
WINDOW_SECONDS = 10 # Aggregation window for "Real Time" feel

def monitor_live():
    print(f"Loading model from {MODEL_PATH}...")
    if not os.path.exists(MODEL_PATH):
        print("Model not found. Run src/train_model.py first.")
        return

    detector = OntapAnomalyDetector()
    detector.load_model(MODEL_PATH)
    
    print(f"Monitoring {LOG_FILE}... (Press Ctrl+C to stop)")
    
    # We'll use a simple polling mechanism
    # In a real system, we'd use 'tail -f' piping or a specialized agent
    # Here, we read the entire file but only process new lines?
    # Simpler: Just parse the file every X seconds and check the LAST window.
    # PROD approach: Keep file handle open.
    
    # 1. Open file at the end
    f = open(LOG_FILE, 'r')
    f.seek(0, 2) # Go to end
    
    parser = LogParser()
    engine = FeatureEngineer()
    
    try:
        while True:
            # Sleep for window size
            time.sleep(WINDOW_SECONDS)
            
            # Read new lines
            new_lines = f.readlines()
            if not new_lines:
                continue
            
            # Parse
            parsed_logs = []
            for line in new_lines:
                p = parser.parse_line(line)
                if p:
                    parsed_logs.append(p)
            
            if not parsed_logs:
                continue
                
            # Feature extraction for this mini-batch
            # NOTE: FeatureEngineer aggregates everything in its buffer.
            # We want just this batch.
            batch_engine = FeatureEngineer()
            batch_engine.ingest_stream(parsed_logs)
            
            # Aggregate into a single summary row for this batch
            # We treat the whole batch as one "window" roughly
            # Or properly resample. Let's resample to 10s.
            
            batch_df = batch_engine.aggregate_window(freq=f"{WINDOW_SECONDS}s")
            
            if batch_df.empty:
                continue
                
            # Predict
            results = detector.predict(batch_df)
            
            # Alert
            for ts, row in results.iterrows():
                score = row['score']
                status = row['is_anomaly']
                
                print(f"[{ts}] Score: {score:.3f} | Errors: {row['error_count']} | Latency: {row['avg_latency']}")
                
                if status == -1:
                    print(f"🚨 ANOMALY DETECTED! 🚨 (Score: {score:.3f})")
                    if row['avg_latency'] > 50:
                        print(f"   -> Potential Cause: High Latency ({row['avg_latency']}ms)")
                    if row['error_count'] > 0:
                        print(f"   -> Potential Cause: Error Burst ({row['error_count']} errors)")

    except KeyboardInterrupt:
        print("\nStopping inference.")
        f.close()

if __name__ == "__main__":
    monitor_live()
