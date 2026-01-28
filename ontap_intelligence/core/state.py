"""
state.py

Maintains the system state and topology (Knowledge Graph).
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, List

logger = logging.getLogger(__name__)

@dataclass
class Asset:
    id: str
    type: str # 'node', 'aggr', 'volume', 'disk', 'util'
    parent_id: Optional[str] = None
    health_score: float = 100.0
    status: str = "ok"

class AssetManager:
    """
    Simple in-memory graph of assets.
    """
    def __init__(self):
        self.assets: Dict[str, Asset] = {}
        self.relations: Dict[str, Set[str]] = {} # parent -> children

    def add_or_update_asset(self, id: str, type: str, parent_id: Optional[str] = None):
        if id not in self.assets:
            self.assets[id] = Asset(id=id, type=type, parent_id=parent_id)
            logger.debug(f"Discovered new asset: {type}:{id} (Parent: {parent_id})")
        
        # Update parent if learned
        if parent_id:
            asset = self.assets[id]
            if asset.parent_id != parent_id:
                asset.parent_id = parent_id
                # Add relation
                if parent_id not in self.relations:
                    self.relations[parent_id] = set()
                self.relations[parent_id].add(id)

    def get_asset(self, id: str) -> Optional[Asset]:
        return self.assets.get(id)

    def get_children(self, parent_id: str) -> List[Asset]:
        if parent_id in self.relations:
            return [self.assets[child_id] for child_id in self.relations[parent_id]]
        return []

    def set_asset_health(self, id: str, score: float, status: str):
        if id in self.assets:
            self.assets[id].health_score = score
            self.assets[id].status = status

# Global State
state = AssetManager()
