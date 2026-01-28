"""
log_generator.py

Generates synthetic NetApp ONTAP EMS logs in Legacy Syslog format.
Format: <PRIVAL>TIMESTAMP [HOSTNAME:Event-name:Event-severity]: MSG
"""

import time
import random
import datetime
from src.patterns import TEMPLATES, NODES, HOSTNAMES

class OntapLogGenerator:
    def __init__(self):
        self.nodes = NODES
        self.hostnames = HOSTNAMES
        
        # Pre-compute lists for weighted random selection
        self.noise_patterns = [k for k in TEMPLATES.keys() if k.startswith("N")]
        self.warning_patterns = [k for k in TEMPLATES.keys() if k.startswith("W")]
        self.failure_patterns = [k for k in TEMPLATES.keys() if k.startswith("F")]

    def _get_prival(self, severity_str):
        """
        Returns a syslog PRIVAL (Priority Value).
        Mapping is arbitrary but consistent for simulation.
        Facility=local0(16) * 8 + Severity(0-7).
        """
        sev_map = {
            "EMERGENCY": 0, "ALERT": 1, "CRITICAL": 2, "ERROR": 3,
            "WARNING": 4, "NOTICE": 5, "INFORMATIONAL": 6, "DEBUG": 7
        }
        severity_code = sev_map.get(severity_str, 6)
        facility = 16 # local0
        return (facility * 8) + severity_code

    def _generate_dynamic_values(self, template_key):
        """
        Generates random values for the placeholders in the message template.
        """
        vals = {}
        
        # IDs and Names
        vals['disk_id'] = f"{random.randint(0, 9)}.{random.randint(0, 24)}"
        vals['shelf_id'] = f"{random.randint(1, 5)}"
        vals['aggr_name'] = f"aggr{random.randint(1, 4)}_{random.choice(['ssd', 'sata'])}"
        vals['raid_group'] = f"rg{random.randint(0, 5)}"
        vals['lif_name'] = f"lif_{random.choice(['data', 'cluster', 'mgmt'])}_{random.randint(100, 999)}"
        vals['port'] = f"e{random.choice(['0a', '0b', '1a', '1b'])}"
        vals['vserver'] = f"svm{random.randint(1, 10)}"
        vals['vol_name'] = f"vol_{random.choice(['finance', 'hr', 'eng', 'marketing'])}_{random.randint(1, 50)}"
        vals['dest_vol'] = f"dp_vol_{random.randint(1, 50)}"
        
        # Metrics
        vals['usage'] = random.randint(95, 99) if template_key == "W01" else random.randint(10, 80)
        vals['latency'] = random.randint(50, 500) if template_key == "W02" else random.randint(1, 10)
        vals['threshold'] = 20
        vals['workload_name'] = f"policy_group_{random.randint(1, 5)}"
        vals['fan_id'] = random.randint(1, 6)
        
        # Textual
        vals['reason'] = random.choice(["Network timeout", "Transfer stalled", "Snapshot missing"])
        vals['trap_event'] = random.choice(["linkUp", "linkDown", "coldStart", "authFailure"])
        vals['trap_dest'] = "192.168.1.10"
        vals['user'] = random.choice(["admin", "ansible_svc", "monitoring"])
        vals['command'] = random.choice(["vol show", "lun map", "snapmirror update", "net int show"])
        vals['scan_type'] = random.choice(["active_fcp", "snapshot_reclaim", "deswizzler"])
        vals['days'] = random.randint(10, 300)
        vals['hours'] = random.randint(0, 23)

        return vals

    def generate_log(self, pattern_id=None, timestamp=None):
        """
        Generates a single log string.
        
        :param pattern_id: specific pattern ID to generate (e.g., 'F01'). If None, random.
        :param timestamp: datetime object. If None, uses current time.
        """
        if not timestamp:
            timestamp = datetime.datetime.now()
        
        # 1. Select Pattern
        if not pattern_id:
            # select random based on weights: 90% Noise, 9% Warning, 1% Failure
            roll = random.random()
            if roll < 0.90:
                pattern_id = random.choice(self.noise_patterns)
            elif roll < 0.99:
                pattern_id = random.choice(self.warning_patterns)
            else:
                pattern_id = random.choice(self.failure_patterns)
        
        template = TEMPLATES[pattern_id]

        # 2. Build Components
        prival = self._get_prival(template['severity'])
        
        # Format: Jan 22 05:21:07
        ts_str = timestamp.strftime("%b %d %H:%M:%S")
        
        hostname = random.choice(self.hostnames)
        node = random.choice(self.nodes)
        
        # Ensure node matches hostname roughly (optional, but adds realism if we care)
        # Assuming ontap-cluster-01 has ontap-cluster-01-01, etc.
        if hostname in node:
            pass # Keep them matching
        else:
             # simple fix to align node to cluster
            base = hostname
            node = f"{base}-0{random.randint(1, 2)}"

        event_name = template['event']
        severity = template['severity']
        
        dynamic_vals = self._generate_dynamic_values(pattern_id)
        message = template['message_template'].format(**dynamic_vals)

        # 3. Assemble
        # <PRIVAL>TIMESTAMP [HOSTNAME:Event-name:Event-severity]: MSG
        log_line = f"<{prival}>{ts_str} [{node}:{event_name}:{severity}]: {message}"
        
        return log_line

if __name__ == "__main__":
    # Quick Test
    gen = OntapLogGenerator()
    print("--- Sample Log ---")
    print(gen.generate_log("F01"))
    print(gen.generate_log("N01"))
