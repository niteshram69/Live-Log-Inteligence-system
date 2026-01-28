"""
simulator.py

Simulates a live ONTAP system by writing logs to a file.
Handles log rotation and simulates different scenarios.
"""

import time
import os
import random
import datetime
from src.log_generator import OntapLogGenerator

LOG_FILE = "logs/ontap_ems.log"
MAX_BYTES = 5 * 1024 * 1024 # 5 MB
ROTATION_COUNT = 5

class Simulator:
    def __init__(self):
        self.generator = OntapLogGenerator()
        
    def _rotate_logs(self):
        """
        Rotates logs: log.4 -> log.5, log.3 -> log.4 ... log -> log.1
        """
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_BYTES:
            print(f"[Simulator] Rotating logs...")
            for i in range(ROTATION_COUNT - 1, 0, -1):
                src = f"{LOG_FILE}.{i}"
                dst = f"{LOG_FILE}.{i+1}"
                if os.path.exists(src):
                    os.rename(src, dst)
            
            if os.path.exists(LOG_FILE):
                os.rename(LOG_FILE, f"{LOG_FILE}.1")

    def run(self):
        print(f"Starting ONTAP Log Simulator. Tail '{LOG_FILE}' to see output.")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        
        try:
            while True:
                # 1. Check rotation
                self._rotate_logs()
                
                # 2. Generate Log
                # 95% chance of being "now", 5% chance of slight delay/burst
                log_line = self.generator.generate_log()
                
                # 3. Write to file
                with open(LOG_FILE, "a") as f:
                    f.write(log_line + "\n")
                
                # 4. Sleep (Variable speed simulation)
                # Traffic burstiness: Random sleep between 0.1s and 2.0s
                sleep_time = random.uniform(0.1, 1.5)
                time.sleep(sleep_time)
                
                # 5. Occasional Burst (Simulation of high activity)
                if random.random() < 0.05:
                    # Write 5-10 logs rapidly
                    for _ in range(random.randint(5, 10)):
                        with open(LOG_FILE, "a") as f:
                            f.write(self.generator.generate_log() + "\n")
                            
        except KeyboardInterrupt:
            print("\nSimulator stopped.")

if __name__ == "__main__":
    sim = Simulator()
    sim.run()
