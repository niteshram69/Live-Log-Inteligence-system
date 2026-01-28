"""
test_generator.py

Unit tests for the OntapLogGenerator.
"""

import unittest
import re
from src.log_generator import OntapLogGenerator

class TestOntapLogGenerator(unittest.TestCase):
    def setUp(self):
        self.gen = OntapLogGenerator()

    def test_log_format_regex(self):
        """
        Verify that generated logs match the expected Syslog regex.
        Format: <PRIVAL>TIMESTAMP [HOSTNAME:Event-name:Event-severity]: MSG
        """
        # Regex from Taxonomy
        log_pattern = re.compile(r"<(\d+)>([A-Z][a-z]{2}\s+\d{2}\s\d{2}:\d{2}:\d{2}) \[(.*?):(.*?):(.*?)]: (.*)")
        
        log_line = self.gen.generate_log("F01")
        match = log_pattern.match(log_line)
        
        self.assertIsNotNone(match, f"Log line did not match regex: {log_line}")
        
        # Check groups
        prival, timestamp, source, event, severity, msg = match.groups()
        self.assertTrue(prival.isdigit())
        self.assertEqual(event, "disk.outOfService")
        self.assertEqual(severity, "ERROR")

    def test_specific_generation(self):
        """Test generating a specific pattern ID."""
        log = self.gen.generate_log("W01")
        self.assertIn("monitor.volume.nearlyFull", log)
        self.assertIn("WARNING", log)

    def test_random_distribution(self):
        """Test that we don't just generate failures."""
        logs = [self.gen.generate_log() for _ in range(100)]
        
        # Simple check to ensure variety
        # It's probabilistic, but highly unlikely 100 random logs are ALL errors or ALL info
        has_info = any("INFORMATIONAL" in l for l in logs)
        has_noise = any("callhome" in l or "audit" in l for l in logs)
        
        self.assertTrue(has_info, "Generated 100 logs but found no INFORMATIONAL (unlikely)")

if __name__ == "__main__":
    unittest.main()
