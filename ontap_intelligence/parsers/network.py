"""
network.py

Parses Network-related events (LIFs, Ports, QoS).
"""

from .base import BaseParser, UnifiedEvent
from ontap_intelligence.core.state import state
import re

class NetworkParser(BaseParser):
    def __init__(self):
        self.patterns = {
            'vifMgr.lif.down': self._parse_lif_down,
            'qos.latency.high': self._parse_qos
        }

    def can_parse(self, event_name: str) -> bool:
        return event_name in self.patterns

    def parse(self, raw: dict) -> UnifiedEvent:
        handler = self.patterns.get(raw['event'])
        if handler:
            return handler(raw)
        return None

    def _parse_lif_down(self, raw: dict) -> UnifiedEvent:
        # LIF lif_data_101 (port e0a) on Vserver svm1 has gone down.
        # Regex to extract components
        # Assuming simplified message from our generator
        # "LIF {lif_name} (port {port}) on Vserver {vserver} has gone down."
        m = re.search(r"LIF (.*?) \(port (.*?)\) on Vserver (.*?) has", raw['message'])
        lif, port, vserver = m.groups() if m else ("unknown", "unknown", "unknown")

        state.add_or_update_asset(lif, "lif", parent_id=raw['node'])

        return UnifiedEvent(
            timestamp=raw['timestamp'],
            timestamp_str=raw['timestamp_str'],
            node=raw['node'],
            subsystem='network',
            event_name=raw['event'],
            severity='ERROR',
            impact_level=9,
            raw_message=raw['message'],
            parsed_fields={'lif': lif, 'port': port, 'vserver': vserver},
            asset_id=lif
        )

    def _parse_qos(self, raw: dict) -> UnifiedEvent:
        # Workload policy_group_1 latency is 45ms
        m = re.search(r"latency is (\d+)ms", raw['message'])
        lat = int(m.group(1)) if m else 0
        
        # "Workload {name}"
        m2 = re.search(r"Workload (.*?) latency", raw['message'])
        workload = m2.group(1) if m2 else "unknown"

        return UnifiedEvent(
            timestamp=raw['timestamp'],
            timestamp_str=raw['timestamp_str'],
            node=raw['node'],
            subsystem='network', # QoS often crosses layers, putting in network/perf
            event_name=raw['event'],
            severity='WARN',
            impact_level=4,
            raw_message=raw['message'],
            parsed_fields={'latency': lat, 'workload': workload},
            asset_id=workload
        )
