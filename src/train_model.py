"""
train_model.py

Generates synthetic history and trains the Isolation Forest model.
"""

import pandas as pd
import os
import shutil
from src.log_generator import OntapLogGenerator
from src.parser import LogParser
from src.feature_engine import FeatureEngineer
from src.anomaly_detector import OntapAnomalyDetector

MODEL_PATH = "models/iso_forest.pkl"
TRAIN_SIZE = 2000 # Number of log lines for training

def generate_training_data():
    """
    Generates a batch of mostly normal logs.
    """
    print(f"Generating {TRAIN_SIZE} synthetic logs...")
    gen = OntapLogGenerator()
    
    # We want mostly normal data for training to establish a baseline
    # But Isolation Forest handles some noise well.
    logs = []
    
    # Simulate 24 hours of normal-ish traffic
    for _ in range(TRAIN_SIZE):
        # Force low probability of failure during training generation logic?
        # The generator has built-in weights (90% Info), which is fine.
        logs.append(gen.generate_log())
        
    return logs

def main():
    # 1. Generate Data
    raw_logs = generate_training_data()
    
    # 2. Parse
    print("Parsing logs...")
    parser = LogParser()
    parsed_logs = [parser.parse_line(line) for line in raw_logs if line]
    
    # 3. Feature Engineering
    print("Extracting features...")
    engine = FeatureEngineer()
    engine.ingest_stream(filter(None, parsed_logs))
    
    # Use 1-minute aggregation
    features_df = engine.aggregate_window(freq="1min")
    print(f"Training data shape: {features_df.shape}")
    
    # 4. Train Model
    print("Training Isolation Forest...")
    detector = OntapAnomalyDetector(contamination=0.01) # Assume 1% anomalies in history
    detector.train(features_df)
    
    # 5. Save
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    detector.save_model(MODEL_PATH)
    print("Done.")

if __name__ == "__main__":
    main()
