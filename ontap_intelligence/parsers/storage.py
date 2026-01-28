"""
storage.py

Parses Storage-related events (Disk, RAID, WAFL).
Updates the AssetManager topology based on discovery.
"""

from .base import BaseParser, UnifiedEvent
from ontap_intelligence.core.state import state
import re

class StorageParser(BaseParser):
    def __init__(self):
        self.patterns = {
            'monitor.volume.nearlyFull': self._parse_vol_full,
            'disk.outOfService': self._parse_disk_fail,
            'raid.aggr.degraded': self._parse_aggr_degraded,
            'wafl.scan.start': self._parse_wafl_scan
        }

    def can_parse(self, event_name: str) -> bool:
        return event_name in self.patterns

    def parse(self, raw: dict) -> UnifiedEvent:
        handler = self.patterns.get(raw['event'])
        if handler:
            return handler(raw)
        return None

    def _normalize_severity(self, sev: str) -> str:
        if sev in ['EMERGENCY', 'ALERT', 'ERROR']: return 'ERROR'
        if sev == 'WARNING': return 'WARN'
        return 'INFO'

    def _parse_vol_full(self, raw: dict) -> UnifiedEvent:
        # Msg: Volume vol_X on aggregate aggr_Y is 99% full.
        m = re.search(r"Volume (.*?) on aggregate (.*?) is (\d+)% full", raw['message'])
        vol_name, aggr_name, usage = m.groups() if m else ("unknown", "unknown", 0)
        
        # Update Topology
        state.add_or_update_asset(aggr_name, "aggr", parent_id=raw['node'])
        state.add_or_update_asset(vol_name, "volume", parent_id=aggr_name)

        return UnifiedEvent(
            timestamp=raw['timestamp'],
            timestamp_str=raw['timestamp_str'],
            node=raw['node'],
            subsystem='storage',
            event_name=raw['event'],
            severity=self._normalize_severity(raw['severity']),
            impact_level=5,
            raw_message=raw['message'],
            parsed_fields={'usage': int(usage), 'limit': 95},
            asset_id=vol_name
        )

    def _parse_disk_fail(self, raw: dict) -> UnifiedEvent:
        # Msg: Disk 1.2 on shelf 1 ...
        m = re.search(r"Disk (.*?) on shelf", raw['message'])
        disk_id = m.group(1) if m else "unknown"
        
        state.add_or_update_asset(disk_id, "disk", parent_id=raw['node'])

        return UnifiedEvent(
            timestamp=raw['timestamp'],
            timestamp_str=raw['timestamp_str'],
            node=raw['node'],
            subsystem='storage',
            event_name=raw['event'],
            severity='ERROR',
            impact_level=8,
            raw_message=raw['message'],
            parsed_fields={'disk_id': disk_id},
            asset_id=disk_id
        )

    def _parse_aggr_degraded(self, raw: dict) -> UnifiedEvent:
        # Msg: Aggregate aggr1 is degraded.
        m = re.search(r"Aggregate (.*?) is degraded", raw['message'])
        aggr_name = m.group(1) if m else "unknown"

        return UnifiedEvent(
            timestamp=raw['timestamp'],
            timestamp_str=raw['timestamp_str'],
            node=raw['node'],
            subsystem='storage',
            event_name=raw['event'],
            severity='ERROR',
            impact_level=9,
            raw_message=raw['message'],
            parsed_fields={'aggr': aggr_name},
            asset_id=aggr_name
        )
        
    def _parse_wafl_scan(self, raw: dict) -> UnifiedEvent:
        # Msg: WAFL scan 'active_fcp' started on volume vol_X.
        m = re.search(r"on volume (.*?)\.", raw['message'])
        vol_name = m.group(1) if m else "unknown"
        
        # We might not know the aggregate here, so just link to Node for now if new
        state.add_or_update_asset(vol_name, "volume", parent_id=raw['node'])

        return UnifiedEvent(
            timestamp=raw['timestamp'],
            timestamp_str=raw['timestamp_str'],
            node=raw['node'],
            subsystem='storage',
            event_name=raw['event'],
            severity='INFO',
            impact_level=1,
            raw_message=raw['message'],
            parsed_fields={'scan': 'active_fcp'},
            asset_id=vol_name
        )
