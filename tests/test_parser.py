"""
test_parser.py

Unit tests for LogParser.
"""

import unittest
import datetime
from src.parser import LogParser

class TestLogParser(unittest.TestCase):
    def setUp(self):
        self.parser = LogParser()

    def test_valid_log(self):
        line = "<131>Jan 22 10:54:47 [ontap-cluster-01-02:snapmirror.dst.updateFailed:ERROR]: Update of destination volume dp_vol_48 failed."
        parsed = self.parser.parse_line(line)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['prival'], 131)
        self.assertEqual(parsed['node'], "ontap-cluster-01-02")
        self.assertEqual(parsed['event'], "snapmirror.dst.updateFailed")
        self.assertEqual(parsed['severity'], "ERROR")
        self.assertEqual(parsed['message'], "Update of destination volume dp_vol_48 failed.")
        self.assertIsInstance(parsed['timestamp'], datetime.datetime)

    def test_malformed_log(self):
        line = "This is just random text not a log"
        parsed = self.parser.parse_line(line)
        self.assertIsNone(parsed)

    def test_timestamp_parsing(self):
        # Just check it returns a datetime and matches values
        line = "<131>Jan 01 12:00:00 [node:ev:INFO]: msg"
        parsed = self.parser.parse_line(line)
        dt = parsed['timestamp']
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 12)

if __name__ == "__main__":
    unittest.main()
