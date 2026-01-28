"""
dashboard.py

Enterprise Command Center for ONTAP Intelligence.
Visualizes Topology, Incidents, and Live Metrics.
"""

import streamlit as st
import pandas as pd
import time
import graphviz
from ontap_intelligence.core.state import state
from ontap_intelligence.intelligence.correlation import correlator

# Note: In a real system, the Dashboard would connect to the running backend via API/DB.
# Here, we import the singletons. Since Streamlit re-runs the script, state persistence
# requires st.session_state or caching if we want to share state with the background threads.
# BUT, since we are running everything in one process for this demo, singletons MIGHT work
# if the Streamlit server process is the same as the ingestor process.
# actually, `streamlit run` spawns a new process. So it won't see the `state` object 
# populated by `src/simulator.py` if that's running separately.
#
# FOR DEMO PURPOSES: We will make this dashboard "Read-Only" from the log file 
# and re-run all the logic internally (Ingest->Parse->Correlate) on the fly for the view window.
# This ensures consistency without complex IPC.

from ontap_intelligence.core.ingestion import LogIngestor
from ontap_intelligence.parsers.service import parser_service
from ontap_intelligence.intelligence.correlation import CorrelationEngine
from ontap_intelligence.core.state import AssetManager
import threading

st.set_page_config(layout="wide", page_title="ONTAP Enterprise Observability")

# --- Simulation Logic (Re-running pipeline for UI) ---
@st.cache_resource
def get_pipeline():
    # specialized separate pipeline for Dashboard
    pm = AssetManager()
    cor = CorrelationEngine()
    return pm, cor

asset_mgr, corr_engine = get_pipeline()

def process_logs_for_ui():
    """Reads the last N lines of the log file and updates local UI state."""
    log_file = "logs/ontap_ems.log"
    import os
    if not os.path.exists(log_file): return []
    
    with open(log_file, "r") as f:
        # Read last 200 lines for speed
        lines = f.readlines()[-200:]
    
    events = []
    # Temporarily hook into our local components
    # We manually drive the parser -> state -> correlator flow
    from ontap_intelligence.parsers.service import parser_service
    
    for line in lines:
        # Parse
        basic = parser_service.raw_parser.parse_line(line)
        if not basic: continue
        
        # Domain Parse
        ue = None
        for dp in parser_service.domain_parsers:
            if dp.can_parse(basic['event']):
                ue = dp.parse(basic) # This specific call UPDATES the global 'state' imported in dp
                # Wait, 'dp' imports 'state' from core.state.
                # If we want to visualize *that* state, we need to ensure we are looking at the same object.
                # Since we are re-running parsing here, the 'state' module imported by storage.py 
                # will be populated in THIS process. So it works!
                break
        
        if ue:
            events.append(ue)
            corr_engine._handle_event("event.unified", ue) # Update local correlator
            
    return events

# --- UI Layout ---

st.title("🏯 ONTAP Enterprise Command Center")

# refresh
if st.button("Refresh Data"):
    st.rerun()

events = process_logs_for_ui()

# Top Row: KPI
col1, col2, col3 = st.columns(3)
col1.metric("Active Incidents", len(corr_engine.buffer)) # Approximation
col2.metric("Assets Discovered", len(state.assets))
criticals = sum(1 for e in events if e.impact_level >= 8)
col3.metric("Critical Events (Last 200)", criticals)

# Tabs
tab1, tab2, tab3 = st.tabs(["Topology Graph", "Incidents & Correlation", "Live Events"])

with tab1:
    st.header("System Topology (Knowledge Graph)")
    # Build Graphviz
    graph = graphviz.Digraph()
    graph.attr(rankdir='LR')
    
    for asset_id, asset in state.assets.items():
        color = "lightblue"
        if asset.type == 'node': color = "lightgrey"
        if asset.type == 'aggr': color = "lightgreen"
        if asset.type == 'disk': color = "white"
        
        graph.node(asset.id, f"{asset.type.upper()}\n{asset.id}", style="filled", fillcolor=color)
        if asset.parent_id:
            graph.edge(asset.parent_id, asset.id)
            
    st.graphviz_chart(graph)

with tab2:
    st.header("Failure Correlation")
    # We iterate manually to match logic since we don't have the mocked bus incidents here easily
    # But let's verify if any correlator logic fired
    # Accessing private methods for demo:
    # We can check specific patterns manually in the Event list for display
    
    st.write("Recent Incidents (Simulated Detection):")
    
    # Simple Manual correlation display for the UI
    for i, e in enumerate(events):
        if e.event_name == 'raid.aggr.degraded':
            # Check previous for disk fail
            prev = events[max(0, i-20):i]
            cause = next((p for p in prev if p.event_name == 'disk.outOfService'), None)
            
            if cause:
                st.error(f"🚨 **INCIDENT LINKED**: Aggregate `{e.asset_id}` Degraded")
                st.markdown(f"**Root Cause**: Disk Failure `{cause.asset_id}` on Node `{cause.node}`")
                st.caption(f"Time Delta: {e.timestamp - cause.timestamp}")
                st.divider()

with tab3:
    st.header("Unified Event Stream")
    # Table of valid events
    data = [{
        "Time": e.timestamp_str,
        "Node": e.node,
        "Subsystem": e.subsystem,
        "Event": e.event_name,
        "Severity": e.severity,
        "Message": e.raw_message
    } for e in events]
    
    st.dataframe(pd.DataFrame(data))

# Auto Refresh
time.sleep(2)
st.rerun()
