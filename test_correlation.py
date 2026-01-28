"""
test_correlation.py

Verifies that the CorrelationEngine detects a Disk Failure -> RAID Cascade.
"""

import time
import logging
import datetime
from ontap_intelligence.core.bus import bus
from ontap_intelligence.parsers.service import parser_service
from ontap_intelligence.intelligence.correlation import correlator

logging.basicConfig(level=logging.INFO)

# Mock Incident Listener
def on_incident(topic, incident):
    print(f"\n[BUS] 🚨 Received Incident: {incident.description}")
    print(f"      Root Cause: {incident.root_cause_event.event_name} ({incident.root_cause_event.asset_id})")

def main():
    print("--- Starting Correlation Test ---")
    
    # 1. Setup
    parser_service.start()
    correlator.start()
    bus.subscribe("event.incident", on_incident)
    
    # 2. Inject Events
    # Event 1: Disk Failure (0s)
    log1 = "<131>Jan 22 12:05:00 [node1:disk.outOfService:ERROR]: Disk 1.2 on shelf 1 failed."
    print(f"Injecting: {log1}")
    bus.publish("log.raw", log1)
    
    time.sleep(1)
    
    # Event 2: RAID Degraded (1s later)
    # This should trigger the correlation rule
    log2 = "<131>Jan 22 12:05:01 [node1:raid.aggr.degraded:ALERT]: Aggregate aggr1 is degraded."
    print(f"Injecting: {log2}")
    bus.publish("log.raw", log2)
    
    # Wait for processing
    time.sleep(2)
    print("--- Test Complete ---")

if __name__ == "__main__":
    main()
