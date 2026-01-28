"""
bus.py

Internal Event Bus for the ONTAP Intelligence Platform.
Decouples ingestion, parsing, and analysis components.
"""

from typing import Callable, List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class EventBus:
    """
    Singleton-style Event Bus.
    Components subscribe to 'topics' (or all events).
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._all_subscribers: List[Callable] = []

    def subscribe(self, topic: str, handler: Callable):
        """Subscribe to a specific topic."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)
        logger.debug(f"Subscribed to topic '{topic}'")

    def subscribe_all(self, handler: Callable):
        """Subscribe to ALL events."""
        self._all_subscribers.append(handler)

    def publish(self, topic: str, payload: Any):
        """
        Publish an event to a topic.
        Payload can be any object (dict, dataclass, etc).
        """
        # Notify specific subscribers
        if topic in self._subscribers:
            for handler in self._subscribers[topic]:
                try:
                    handler(topic, payload)
                except Exception as e:
                    logger.error(f"Error in handler for topic '{topic}': {e}")

        # Notify global subscribers
        for handler in self._all_subscribers:
            try:
                handler(topic, payload)
            except Exception as e:
                logger.error(f"Error in global handler: {e}")

# Global instance
bus = EventBus()
