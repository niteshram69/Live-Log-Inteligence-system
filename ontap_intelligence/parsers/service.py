"""
service.py

Parser Service Orchestrator.
Listens to 'log.raw', parses it, and publishes 'event.unified'.
"""

from ontap_intelligence.core.bus import bus
from src.parser import LogParser as RawRegexParser # Reuse our Phase 3 regex
from .storage import StorageParser
from .network import NetworkParser
import logging

logger = logging.getLogger(__name__)

class ParserService:
    def __init__(self):
        self.raw_parser = RawRegexParser()
        self.domain_parsers = [
            StorageParser(),
            NetworkParser()
        ]
        
    def start(self):
        bus.subscribe("log.raw", self._handle_raw_log)
        logger.info("ParserService started.")

    def _handle_raw_log(self, topic, payload: str):
        # 1. Regex Parse (Basic Fields)
        basic = self.raw_parser.parse_line(payload)
        if not basic:
            return # Skip junk

        # 2. Domain Parse (Normalization & Topology)
        unified_event = None
        for dp in self.domain_parsers:
            if dp.can_parse(basic['event']):
                unified_event = dp.parse(basic)
                break
        
        # 3. Fallback (System events, noise)
        if not unified_event:
            # Create a generic event
            from .base import UnifiedEvent
            unified_event = UnifiedEvent(
                timestamp=basic['timestamp'],
                timestamp_str=basic['timestamp_str'],
                node=basic['node'],
                subsystem='system',
                event_name=basic['event'],
                severity=basic['severity'], # unnormalized
                impact_level=0,
                raw_message=basic['message'],
                parsed_fields={},
                asset_id=None
            )

        # 4. Publish Unified Event
        bus.publish("event.unified", unified_event)
        
        # Debug print (for demo)
        if unified_event.impact_level > 5:
            logger.info(f"High Impact Event: {unified_event.subsystem.upper()} - {unified_event.event_name}")

# Global instance
parser_service = ParserService()
