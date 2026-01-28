"""
dashboard.py

Streamlit Dashboard for ONTAP Log Anomaly Detection.
Run with: streamlit run src/dashboard.py
"""

import streamlit as st
import pandas as pd
import time
import altair as alt
import os
import joblib

# Import our project modules
# Note: When running streamlit, the CWD is usually the project root if run from there.
from src.parser import LogParser
from src.feature_engine import FeatureEngineer
from src.anomaly_detector import OntapAnomalyDetector

# --- Configuration ---
LOG_FILE = "logs/ontap_ems.log"
MODEL_PATH = "models/iso_forest.pkl"
REFRESH_RATE = 2  # seconds
WINDOW_SIZE_MINUTES = 10 # View last X minutes

st.set_page_config(
    page_title="ONTAP Anomaly Detection",
    page_icon="🔍",
    layout="wide"
)

# --- Helper Functions ---
@st.cache_resource
def load_detector():
    if os.path.exists(MODEL_PATH):
        try:
            detector = OntapAnomalyDetector()
            detector.load_model(MODEL_PATH)
            return detector
        except Exception as e:
            st.error(f"Error loading model: {e}")
            return None
    return None

def read_and_process_logs():
    """
    Reads the entire log file and processes it using the existing pipeline.
    In a high-throughput prod env, this would read from a DB or sliding window buffer.
    """
    if not os.path.exists(LOG_FILE):
        return pd.DataFrame()

    # 1. Parse
    parser = LogParser()
    logs = list(parser.parse_file(LOG_FILE))
    
    if not logs:
        return pd.DataFrame()

    # 2. Features
    engine = FeatureEngineer()
    engine.ingest_stream(logs)
    
    # Aggregate to 10-second windows for granular visualization
    df = engine.aggregate_window(freq="10s")
    
    return df

# --- Main Dashboard ---

st.title("🛡️ ONTAP Log Anomaly Detection")

# Sidebar
st.sidebar.header("Configuration")
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
window_min = st.sidebar.slider("Time Window (Minutes)", 5, 60, 10)

# Load Model
detector = load_detector()
if not detector:
    st.sidebar.warning("⚠️ ML Model not found. Run training first.")

# Main Loop Area
placeholder = st.empty()

while True:
    with placeholder.container():
        # Get Data
        df = read_and_process_logs()
        
        if df.empty:
            st.warning("No logs found. Is the simulator running?")
            time.sleep(REFRESH_RATE)
            continue

        # Filter by Time Window
        now = df.index.max()
        cutoff = now - pd.Timedelta(minutes=window_min)
        view_df = df[df.index >= cutoff].copy()

        # Run Inference
        if detector:
            results = detector.predict(view_df)
        else:
            results = view_df.copy()
            results['is_anomaly'] = 1 # Default normal
            results['score'] = 0.5

        # --- KPI Metrics Row ---
        last_row = results.iloc[-1]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Log Rate (10s)", f"{int(last_row['log_count'])}")
        c2.metric("Errors (10s)", f"{int(last_row['error_count'])}", 
                  f"{int(last_row['error_count'])}", delta_color="inverse")
        c3.metric("Avg Latency", f"{last_row['avg_latency']:.1f} ms",
                  f"{last_row['avg_latency'] - 20:.1f}" if last_row['avg_latency'] > 0 else None, delta_color="inverse")
        
        # Anomaly Status
        is_anom = last_row['is_anomaly'] == -1
        status_color = "red" if is_anom else "green"
        status_text = "CRITICAL ANOMALY" if is_anom else "SYSTEM NORMAL"
        c4.markdown(f"### Status: :{status_color}[{status_text}]")

        # --- Charts ---
        # 1. Latency & Errors over time
        st.subheader("Performance & Stability")
        
        # Reshape for Altair (Metric selection)
        chart_data = view_df.reset_index()
        
        base = alt.Chart(chart_data).encode(x='timestamp:T')
        
        line_latency = base.mark_line(color='#FFA500').encode(
            y=alt.Y('avg_latency', title='Latency (ms)'),
            tooltip=['timestamp', 'avg_latency']
        )
        
        bar_errors = base.mark_bar(color='#FF4B4B', opacity=0.5).encode(
            y=alt.Y('error_count', title='Errors'),
            tooltip=['timestamp', 'error_count']
        )

        c_perf = alt.layer(line_latency, bar_errors).resolve_scale(y='independent').properties(height=300)
        st.altair_chart(c_perf, use_container_width=True)

        # 2. Anomaly Score
        if detector:
            st.subheader("Anomaly Detection Model")
            results_reset = results.reset_index()
            
            # Line of scores
            score_line = alt.Chart(results_reset).mark_line(color='#1E90FF').encode(
                x='timestamp:T',
                y=alt.Y('score', title='Anomaly Score (Lower is bad)'),
                tooltip=['timestamp', 'score']
            )
            
            # Points for anomalies
            anomalies = results_reset[results_reset['is_anomaly'] == -1]
            if not anomalies.empty:
                anomaly_points = alt.Chart(anomalies).mark_circle(size=100, color='red').encode(
                    x='timestamp:T',
                    y='score',
                    tooltip=['timestamp', 'score', 'error_count']
                )
                c_anom = score_line + anomaly_points
            else:
                c_anom = score_line
                
            st.altair_chart(c_anom, use_container_width=True)

        # --- Recent Alerts ---
        st.subheader("Recent Alerts (Last 10 Events)")
        # Show rows where error > 0 or is_warning or anomaly
        alerts = results[ (results['error_count'] > 0) | (results['warning_count'] > 0) | (results['is_anomaly'] == -1) ]
        if not alerts.empty:
            st.dataframe(alerts.tail(10).sort_index(ascending=False))
        else:
            st.info("No active alerts in window.")

    if not auto_refresh:
        break
    
    time.sleep(REFRESH_RATE)
