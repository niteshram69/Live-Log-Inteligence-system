"""
test_ml_flow.py

Verifies that the MLService detects anomalies from the UnifiedEvent stream.
"""

import time
import logging
from ontap_intelligence.core.bus import bus
from ontap_intelligence.parsers.service import parser_service
from ontap_intelligence.intelligence.ml_models import ml_service

logging.basicConfig(level=logging.INFO)

def main():
    print("--- Starting ML Flow Test ---")
    
    # Start Services
    parser_service.start()
    ml_service.start()
    
    # Inject a burst of High Latency logs to trigger ML
    # We need to fill the window (10s window in code, checks every window end)
    # But for test, we just need enough events to make the aggregate look bad.
    
    log_template = "<134>Jan 22 12:10:{:02d} [node1:qos.latency.high:NOTICE]: Workload policy_group_1 latency is 200ms (Threshold: 20ms)."
    
    print("Injecting latency burst...")
    for i in range(5):
        log = log_template.format(i)
        bus.publish("log.raw", log)
        
    print("Waiting for ML window (10s)...")
    time.sleep(11) # Wait for window to close and predict
    
    print("--- Test Complete ---")

if __name__ == "__main__":
    main()
