"""
anomaly_detector.py

Wraps the Isolation Forest algorithm for ONTAP log anomaly detection.
"""

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

class OntapAnomalyDetector:
    def __init__(self, contamination=0.05):
        """
        :param contamination: Expected proportion of outliers in the dataset.
        """
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42
        )
        self.features = [
            'log_count', 
            'error_count', 
            'warning_count', 
            'vol_full_events', 
            'avg_latency', 
            'unique_nodes'
        ]

    def train(self, df):
        """
        Trains the model on a historical DataFrame.
        Expected columns: Same as self.features
        """
        # Select only relevant numeric features
        X = df[self.features].fillna(0)
        self.model.fit(X)
        print("Model trained successfully.")

    def predict(self, df):
        """
        Returns a DataFrame with 'anomaly_score' and 'is_anomaly'.
        Output:
            - anomaly_score: Lower is more anomalous.
            - is_anomaly: -1 for anomaly, 1 for normal.
        """
        X = df[self.features].fillna(0)
        
        # decision_function: Average anomaly score of X of the base classifiers.
        # The anomaly score of an input sample is computed as
        # the mean anomaly score of the trees in the forest.
        # Measure of normality of an observation.
        # Low values mean anomaly.
        scores = self.model.decision_function(X)
        preds = self.model.predict(X)

        results = df.copy()
        results['score'] = scores
        results['is_anomaly'] = preds # -1 = anomaly
        
        return results

    def save_model(self, filepath):
        joblib.dump(self.model, filepath)
        print(f"Model saved to {filepath}")

    def load_model(self, filepath):
        self.model = joblib.load(filepath)
        print(f"Model loaded from {filepath}")
