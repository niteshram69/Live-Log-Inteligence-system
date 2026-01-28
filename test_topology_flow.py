"""
test_topology_flow.py

Verifies that logs flow through ParserService and update the Asset Topology.
"""

import time
import logging
from ontap_intelligence.core.bus import bus
from ontap_intelligence.core.state import state
from ontap_intelligence.parsers.service import parser_service

# Setup logging to see our components working
logging.basicConfig(level=logging.INFO)

def main():
    print("--- Starting Topology Flow Test ---")
    
    # Start Services
    parser_service.start()
    
    # Simulate Ingestion (Publish direct raw log)
    # Vol full log implies: Node -> Aggregate -> Volume dependency
    raw_log = "<132>Jan 22 12:00:00 [node1:monitor.volume.nearlyFull:WARNING]: Volume vol_finance on aggregate aggr_ssd_1 is 98% full."
    
    print(f"Injecting: {raw_log}")
    bus.publish("log.raw", raw_log)
    
    # Allow processing
    time.sleep(1)
    
    # Check Topology
    print("\n--- Inspecting Knowledge Graph ---")
    vol_asset = state.get_asset("vol_finance")
    aggr_asset = state.get_asset("aggr_ssd_1")
    
    if vol_asset:
        print(f"✅ Found Volume: {vol_asset}")
    else:
        print("❌ Volume not found in State!")

    if aggr_asset:
        print(f"✅ Found Aggregate: {aggr_asset}")
        print(f"   Parent Node: {aggr_asset.parent_id}")
    else:
        print("❌ Aggregate not found in State!")

    # Verify dependency
    if vol_asset and vol_asset.parent_id == "aggr_ssd_1":
        print("✅ Volume -> Aggregate dependency linked correctly.")
    else:
        print(f"❌ Dependency mismatch (Parent: {vol_asset.parent_id if vol_asset else 'None'})")

if __name__ == "__main__":
    main()
