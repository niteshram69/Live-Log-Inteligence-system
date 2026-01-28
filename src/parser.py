"""
parser.py

Parses raw legacy-netapp syslog lines into structured dictionaries.
"""

import re
import datetime

class LogParser:
    def __init__(self):
        # Format: <PRIVAL>TIMESTAMP [HOSTNAME:Event-name:Event-severity]: MSG
        # Regex explanation:
        # <(\d+)>                         -> Prival
        # ([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2}) -> Timestamp (Jan 22 10:54:47)
        # \s\[(.*?):                      -> Node/Hostname (start of bracket to first colon)
        # (.*?):                          -> Event Name (between colons)
        # (.*?)\]:                        -> Severity (between colon and closing bracket)
        # \s(.*)                          -> Message (rest of line)
        self.log_pattern = re.compile(r"<(\d+)>([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2})\s\[(.*?):(.*?):(.*?)]: (.*)")

    def _parse_timestamp(self, ts_str):
        """
        Parses syslog timestamp (Jan 22 10:54:47) into a datetime object.
        Note: Syslog doesn't have year. We assume current year.
        If the parsed date is in the future (e.g., Dec 31 when today is Jan 1), 
        subtract one year.
        """
        now = datetime.datetime.now()
        year = now.year
        
        # Parse: "Jan 22 10:54:47"
        try:
            dt = datetime.datetime.strptime(f"{year} {ts_str}", "%Y %b %d %H:%M:%S")
            
            # Handle year rollover (if log is Dec 31 and we are Jan 1)
            # If parsed time is > 2 days in future, assume previous year
            if dt > now + datetime.timedelta(days=2):
                dt = dt.replace(year=year - 1)
                
            return dt
        except ValueError:
            return None

    def parse_line(self, line):
        """
        Parses a single log line.
        Returns a dict or None if invalid.
        """
        line = line.strip()
        if not line:
            return None

        match = self.log_pattern.match(line)
        if not match:
            return None

        prival, ts_str, node, event, severity, message = match.groups()

        return {
            "prival": int(prival),
            "timestamp": self._parse_timestamp(ts_str),
            "timestamp_str": ts_str, # Keep original just in case
            "node": node,
            "event": event,
            "severity": severity,
            "message": message
        }

    def parse_file(self, filepath):
        """
        Generator that yields parsed logs from a file.
        """
        with open(filepath, 'r') as f:
            for line in f:
                parsed = self.parse_line(line)
                if parsed:
                    yield parsed
