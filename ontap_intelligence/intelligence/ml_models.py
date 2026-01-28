"""
ml_models.py

Machine Learning Service for Anomaly Detection.
Listens to: 'event.unified'
Publishes: 'event.anomaly'
"""

from ontap_intelligence.core.bus import bus
from ontap_intelligence.parsers.base import UnifiedEvent
import pandas as pd
import joblib
import os
import datetime
import logging
from typing import List

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self, model_path="models/iso_forest.pkl"):
        self.model_path = model_path
        self.model = None
        self.buffer: List[UnifiedEvent] = []
        self.window_size = datetime.timedelta(seconds=10) # 10s aggregation for live ML
        self.last_predict_time = datetime.datetime.now()

    def start(self):
        # Load Model
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                logger.info("ML Model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
        else:
            logger.warning("ML Model not found. Anomaly detection disabled.")

        bus.subscribe("event.unified", self._handle_event)
        logger.info("MLService started.")

    def _handle_event(self, topic, event: UnifiedEvent):
        self.buffer.append(event)
        
        # Check if window closed
        now = datetime.datetime.now()
        if now - self.last_predict_time >= self.window_size:
            self._run_inference()
            self.last_predict_time = now
            self.buffer = [] # Clear buffer after window

    def _run_inference(self):
        if not self.model or not self.buffer:
            return

        # 1. Feature Engineering (On the fly)
        # We need to map UnifiedEvents back to the features the model expects:
        # [log_count, error_count, warning_count, vol_full_events, avg_latency, unique_nodes]
        
        df = pd.DataFrame([vars(e) for e in self.buffer])
        
        # Helper to check event type
        df['is_error'] = df['severity'].apply(lambda s: 1 if s == 'ERROR' else 0)
        df['is_warning'] = df['severity'].apply(lambda s: 1 if s == 'WARN' else 0)
        df['is_vol_full'] = df['event_name'] == 'monitor.volume.nearlyFull'
        
        # Extract latency
        def get_latency(e):
            return e.parsed_fields.get('latency', 0)
        
        df['latency_val'] = df.apply(lambda row: row['parsed_fields'].get('latency', 0), axis=1)

        # Aggregate
        features = pd.DataFrame([{
            'log_count': len(df),
            'error_count': df['is_error'].sum(),
            'warning_count': df['is_warning'].sum(),
            'vol_full_events': df['is_vol_full'].sum(),
            'avg_latency': df['latency_val'].mean(),
            'unique_nodes': df['node'].nunique()
        }]).fillna(0)

        # 2. Predict
        try:
            # Reorder columns to match training
            cols = ['log_count', 'error_count', 'warning_count', 'vol_full_events', 'avg_latency', 'unique_nodes']
            X = features[cols]
            
            score = self.model.decision_function(X)[0]
            pred = self.model.predict(X)[0]

            if pred == -1:
                # Anomaly!
                self._publish_anomaly(score, features.iloc[0])

        except Exception as e:
            logger.error(f"Inference error: {e}")

    def _publish_anomaly(self, score, feats):
        # Generate Explanation
        reasons = []
        if feats['error_count'] > 2: reasons.append(f"High Error Rate ({int(feats['error_count'])})")
        if feats['avg_latency'] > 50: reasons.append(f"High Latency ({feats['avg_latency']:.1f}ms)")
        if feats['vol_full_events'] > 0: reasons.append("Volume Capacity Events")
        
        explanation = ", ".join(reasons) if reasons else "Unknown deviation from baseline"

        anomaly_event = {
            "type": "anomaly",
            "score": score,
            "explanation": explanation,
            "timestamp": datetime.datetime.now(),
            "metrics": feats.to_dict()
        }
        
        bus.publish("event.anomaly", anomaly_event)
        logger.info(f"🤖 ML ANOMALY: Score {score:.3f} | {explanation}")

# Global
ml_service = MLService()
