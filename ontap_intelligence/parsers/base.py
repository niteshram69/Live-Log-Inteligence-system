"""
base.py

Base Parser class and Unified Event definition.
"""

from dataclasses import dataclass
from typing import Optional, Dict
import datetime

@dataclass
class UnifiedEvent:
    """
    Normalized Event Schema for the Enterprise Platform.
    """
    timestamp: datetime.datetime
    timestamp_str: str
    node: str
    subsystem: str      # 'storage', 'network', 'system', 'security'
    event_name: str
    severity: str       # Normalized: ERROR, WARN, INFO
    impact_level: int   # 0-10 (10 = Outage)
    raw_message: str
    parsed_fields: Dict # Extracted dynamic values (vol_name, latency, etc.)
    asset_id: Optional[str] = None # The primary asset affected (e.g., 'vol_finance')

class BaseParser:
    def can_parse(self, event_name: str) -> bool:
        """Returns True if this parser handles this event type."""
        return False

    def parse(self, raw_data: dict) -> Optional[UnifiedEvent]:
        """
        Input: Dictionary from the raw regex parser (LogParser).
        Output: Normalized UnifiedEvent.
        """
        raise NotImplementedError
