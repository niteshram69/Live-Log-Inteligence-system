# ONTAP Log Taxonomy & Failure Patterns

## 1. Log Format Specification
We will use the **NetApp Legacy Syslog Format** for its distinct structure.

**Format:**
`<PRIVAL>TIMESTAMP [HOSTNAME:Event-name:Event-severity]: MSG`

**Example:**
`<182>Jan 22 05:21:07 ontap-cluster-01 [node1:callhome.snmp.trap.sent:INFORMATIONAL]: An SNMP trap for event 'callhome.snmp.trap.sent' was sent to '192.168.1.100'.`

## 2. Field Taxonomy

| Field | Regex Group | Description | Example |
|-------|-------------|-------------|---------|
| **Prival** | `<(\d+)>` | Syslog priority value (Facility * 8 + Severity). | `182` |
| **Timestamp** | `([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2})` | Local time (MMM dd HH:mm:ss). | `Jan 22 05:21:07` |
| **Hostname** | `\s([a-zA-Z0-9-]+)\s` | Cluster or Node name. | `ontap-cluster-01` |
| **Source Node** | `\[(.*?):` | The specific node generating the event. | `node1` |
| **Event Name** | `:(.*?):` | Dot-separated event identifier. | `monitor.volume.nearlyFull` |
| **Severity** | `:(.*?)\]:` | Text severity level. | `ERROR`, `INFORMATIONAL` |
| **Message** | `\s(.*)` | Free-text description of the event. | `Volume vol1 on aggregate aggr1 is nearly full.` |

## 3. Failure Patterns (Simulation Targets)

These patterns represent "signals" embedded in the noise of normal operations.

### A. Critical Failures (High Severity)
| Pattern ID | Event Name | Severity | Description | Trigger Frequency |
|------------|------------|----------|-------------|-------------------|
| **F01** | `disk.outOfService` | ERROR | Physical disk failure. Often preceded by latency spikes. | Rare (0.1%) |
| **F02** | `raid.aggr.degraded` | ALERT | RAID group degradation due to disk loss. | Rare (Follows F01) |
| **F03** | `vifMgr.lif.down` | EMERGENCY | Network interface failure. Immediate connectivity loss. | Rare (0.5%) |
| **F04** | `nvram.battery.low` | EMERGENCY | Hardware risk. NVRAM battery needs replacement. | Very Rare |

### B. Warnings & precursors (Medium Severity)
| Pattern ID | Event Name | Severity | Description | Trigger Frequency |
|------------|------------|----------|-------------|-------------------|
| **W01** | `monitor.volume.nearlyFull`| WARNING | Volume capacity >95%. Precursor to write failures. | Occasional (5%) |
| **W02** | `qos.latency.high` | NOTICE | (Synthetic) Latency breach. Performance throttling. | Periodic bursts |
| **W03** | `snapmirror.dst.updateFailed` | ERROR | Replication failure. Risk of RPO violation. | Occasional (2%) |
| **W04** | `chassis.fan.failure` | ALERT | Cooling issue. Can lead to thermal shutdown. | Rare |

### C. Operational Noise (Low Severity)
| Pattern ID | Event Name | Severity | Description | Trigger Frequency |
|------------|------------|----------|-------------|-------------------|
| **N01** | `callhome.snmp.trap.sent` | INFO | Routine telemetry. Top noise generator. | Frequent (50%) |
| **N02** | `audit.cmd.create` | INFO | User activity/CLI commands. | Frequent (20%) |
| **N03** | `wafl.scan.start` | NOTICE | Background filesystem scan. | Periodic |

## 4. Anomaly Scenarios
1.  **" The Cascading Failure"**: Latency warnings (W02) -> Disk Failure (F01) -> RAID Degraded (F02).
2.  **"Capacity Crisis"**: Slow creep of volume full (W01) -> repeated daily frequencies -> Sudden spike in Snapshot auto-delete logs.
3.  **"Vscan Storm"**: Sudden burst of `Nblade.vscanWorkQueueOverloaded` indicating antivirus bottleneck.
