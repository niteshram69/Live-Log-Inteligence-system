"""
patterns.py

This module contains the configuration for the ONTAP log generator.
It defines the EMS event templates and failure scenarios.
"""

# Common fields
NODES = ["ontap-cluster-01-01", "ontap-cluster-01-02", "ontap-cluster-02-01", "ontap-cluster-02-02"]
HOSTNAMES = ["ontap-cluster-01", "ontap-cluster-02"]

# Log Level Weights (Probability of occurrence in normal operation)
SEVERITY_WEIGHTS = {
    "INFORMATIONAL": 0.70,
    "NOTICE": 0.20,
    "WARNING": 0.05,
    "ERROR": 0.03,
    "ALERT": 0.01,
    "EMERGENCY": 0.01
}

# -------------------------------------------------------------------------
# Event Templates
# Dictionary Key: Pattern ID (from Log Taxonomy)
# -------------------------------------------------------------------------
TEMPLATES = {
    # --- Critical Failures ---
    "F01": {
        "event": "disk.outOfService",
        "severity": "ERROR",
        "message_template": "Disk {disk_id} on shelf {shelf_id} has failed and is being taken offline.",
        "category": "hardware"
    },
    "F02": {
        "event": "raid.aggr.degraded",
        "severity": "ALERT",
        "message_template": "Aggregate {aggr_name} is degraded. {raid_group} is missing a disk.",
        "category": "raid"
    },
    "F03": {
        "event": "vifMgr.lif.down",
        "severity": "EMERGENCY",
        "message_template": "LIF {lif_name} (port {port}) on Vserver {vserver} has gone down.",
        "category": "network"
    },
     "F04": {
        "event": "nvram.battery.low",
        "severity": "EMERGENCY",
        "message_template": "The NVRAM battery is critically low. Immediate replacement required.",
        "category": "hardware"
    },

    # --- Warnings & Precursors ---
    "W01": {
        "event": "monitor.volume.nearlyFull",
        "severity": "WARNING",
        "message_template": "Volume {vol_name} on aggregate {aggr_name} is {usage}% full.",
        "category": "capacity"
    },
    "W02": {
        "event": "qos.latency.high",
        "severity": "NOTICE",
        "message_template": "Workload {workload_name} latency is {latency}ms (Threshold: {threshold}ms).",
        "category": "performance"
    },
    "W03": {
        "event": "snapmirror.dst.updateFailed",
        "severity": "ERROR",
        "message_template": "Update of destination volume {dest_vol} failed. Reason: {reason}.",
        "category": "replication"
    },
    "W04": {
        "event": "chassis.fan.failure",
        "severity": "ALERT",
        "message_template": "Fan module {fan_id} has failed. Chassis temperature rising.",
        "category": "hardware"
    },

    # --- Operational Noise (Normal Stuff) ---
    "N01": {
        "event": "callhome.snmp.trap.sent",
        "severity": "INFORMATIONAL",
        "message_template": "An SNMP trap for event '{trap_event}' was sent to '{trap_dest}'.",
        "category": "telemetry"
    },
    "N02": {
        "event": "audit.cmd.create",
        "severity": "INFORMATIONAL",
        "message_template": "User '{user}' executed command '{command}'.",
        "category": "audit"
    },
    "N03": {
        "event": "wafl.scan.start",
        "severity": "NOTICE",
        "message_template": "WAFL scan '{scan_type}' started on volume {vol_name}.",
        "category": "system"
    },
    "N04": {
        "event": "kern.uptime.info",
        "severity": "INFORMATIONAL",
        "message_template": "System uptime is {days} days, {hours} hours.",
        "category": "system"
    }
}
