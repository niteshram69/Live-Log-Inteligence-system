"""
ingestion.py

Handles data ingestion from various sources (File, UDP).
Publishes raw log lines to the Event Bus under topic 'log.raw'.
"""

import time
import os
import threading
from typing import Optional
from ontap_intelligence.core.bus import bus
import logging

logger = logging.getLogger(__name__)

class LogIngestor:
    def __init__(self, config: dict):
        self.config = config
        self.source_file = config['ingestion']['source_file']
        self.mode = config['ingestion']['mode']
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Starts the ingestion loop in a background thread."""
        logger.info(f"Starting LogIngestor in '{self.mode}' mode...")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the ingestion loop."""
        logger.info("Stopping LogIngestor...")
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _run(self):
        if self.mode == 'tail':
            self._run_tail()
        elif self.mode == 'replay':
            self._run_replay()
        else:
            logger.error(f"Unknown ingestion mode: {self.mode}")

    def _run_tail(self):
        """
        Similar to 'tail -f'. Reads new lines as they are written.
        """
        if not os.path.exists(self.source_file):
            logger.warning(f"Source file {self.source_file} not found. Waiting...")
            while not os.path.exists(self.source_file) and not self._stop_event.is_set():
                time.sleep(1)
        
        # Open file
        with open(self.source_file, 'r') as f:
            # Go to end of file to start reading only NEW logs
            f.seek(0, 2)
            
            while not self._stop_event.is_set():
                line = f.readline()
                if line:
                    # Publish stripped line
                    bus.publish("log.raw", line.strip())
                else:
                    time.sleep(self.config['ingestion']['poll_interval'])

    def _run_replay(self):
        """
        Reads from beginning, potentially with time delays (not implemented yet).
        """
        logger.info("Replay mode: processing entire file.")
        if not os.path.exists(self.source_file):
             logger.error("Source file not found for replay.")
             return

        with open(self.source_file, 'r') as f:
            for line in f:
                if self._stop_event.is_set():
                    break
                bus.publish("log.raw", line.strip())
                # Simulate processing speed if needed
                # time.sleep(0.01) 
