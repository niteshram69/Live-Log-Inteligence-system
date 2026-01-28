"""
correlation.py

Correlates UnifiedEvents to detect incidents (Failure Cascades).
Listens to: 'event.unified'
Publishes: 'event.incident'
"""

from ontap_intelligence.core.bus import bus
from ontap_intelligence.core.state import state
from ontap_intelligence.parsers.base import UnifiedEvent
from dataclasses import dataclass, field
from typing import List, Dict
import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class Incident:
    id: str
    description: str
    severity: str
    root_cause_event: UnifiedEvent
    related_events: List[UnifiedEvent] = field(default_factory=list)
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

class CorrelationEngine:
    def __init__(self, window_seconds=60):
        self.window = datetime.timedelta(seconds=window_seconds)
        self.buffer: List[UnifiedEvent] = []
        
    def start(self):
        bus.subscribe("event.unified", self._handle_event)
        logger.info("CorrelationEngine started.")

    def _handle_event(self, topic, event: UnifiedEvent):
        # 1. Add to buffer
        self.buffer.append(event)
        self._prune_buffer()
        
        # 2. Check for patterns
        self._check_disk_raid_cascade(event)

    def _prune_buffer(self):
        """Remove old events outside the window."""
        if not self.buffer: return
        now = self.buffer[-1].timestamp
        cutoff = now - self.window
        self.buffer = [e for e in self.buffer if e.timestamp >= cutoff]

    def _check_disk_raid_cascade(self, current_event: UnifiedEvent):
        """
        Scenario: RAID Group Degraded (Current) -> Caused by Disk Failure (Past)
        """
        if current_event.event_name == 'raid.aggr.degraded':
            # Look for recent disk failure on same NODE
            # In a real system, we'd check if the disk belongs to the aggregate (Topology query)
            # For now, simplistic Node correlation
            
            # Find recent 'disk.outOfService' on same node
            candidates = [
                e for e in self.buffer 
                if e.event_name == 'disk.outOfService' 
                and e.node == current_event.node
                and e != current_event
            ]
            
            if candidates:
                # Found the root cause!
                root_cause = candidates[-1] # Most recent disk fail
                
                incident = Incident(
                    id=f"INC-{int(datetime.datetime.now().timestamp())}",
                    description=f"Aggregate {current_event.asset_id} degraded due to Disk Failure {root_cause.asset_id}",
                    severity="CRITICAL",
                    root_cause_event=root_cause,
                    related_events=[current_event]
                )
                
                bus.publish("event.incident", incident)
                logger.info(f"🔥 INCIDENT DETECTED: {incident.description}")

# Global Instance
correlator = CorrelationEngine()
