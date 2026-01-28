"""
test_ingestion_flow.py

Verifies that LogIngestor reads from 'logs/ontap_ems.log' and publishes to EventBus.
"""

import time
import os
import yaml
from ontap_intelligence.core.ingestion import LogIngestor
from ontap_intelligence.core.bus import bus

# Load Config
with open("ontap_intelligence/config/settings.yaml", "r") as f:
    config = yaml.safe_load(f)

# Mock Listener
def on_raw_log(topic, payload):
    print(f"[BUS-RECEIVED] {topic}: {payload}")

def main():
    print("--- Starting Ingestion Test ---")
    
    # Subscribe
    bus.subscribe("log.raw", on_raw_log)
    
    # Start Ingestor
    ingestor = LogIngestor(config)
    ingestor.start()
    
    # Allow it to run for 5 seconds
    # Assuming simulator is running in background and writing to logs/ontap_ems.log
    time.sleep(5)
    
    ingestor.stop()
    print("--- Test Complete ---")

if __name__ == "__main__":
    main()
