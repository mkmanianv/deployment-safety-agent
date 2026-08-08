import sqlite3
import random
import os
from datetime import datetime, timedelta

os.makedirs("data", exist_ok=True)
conn = sqlite3.connect("data/incidents.db")
cur = conn.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS services (
    id TEXT PRIMARY KEY,
    name TEXT,
    team TEXT,
    criticality TEXT,
    region TEXT
);
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    service_id TEXT,
    type TEXT,
    message TEXT,
    fired_at TEXT,
    resolved INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS change_freezes (
    id TEXT PRIMARY KEY,
    start_time TEXT,
    end_time TEXT,
    region TEXT,
    reason TEXT
);
CREATE TABLE IF NOT EXISTS deployments (
    id TEXT PRIMARY KEY,
    service_id TEXT,
    version TEXT,
    deployed_at TEXT,
    outcome TEXT
);
""")

services = [
    ("svc-payments", "payments-service", "payments", "P1", "ap-mumbai-1"),
    ("svc-auth", "auth-service", "platform", "P1", "ap-mumbai-1"),
    ("svc-deploy", "deployment-svc", "infra", "P2", "ap-hyderabad-1"),
    ("svc-config", "config-manager", "infra", "P2", "us-ashburn-1"),
    ("svc-notify", "notification-svc", "platform", "P3", "uk-london-1"),
]
cur.executemany(
    "INSERT OR IGNORE INTO services VALUES(?,?,?,?,?)", services
)

alerts = [
    ("alt-001", "svc-payments", "CPU_HIGH",
     "CPU at 92% for 10 minutes", 
     datetime.now().isoformat(), 0),
    ("alt-002", "svc-auth", "LATENCY_SPIKE",
     "P95 latency 8000ms, threshold 500ms",
     datetime.now().isoformat(), 0),
    ("alt-003", "svc-notify", "DISK_FULL",
     "Disk at 95% capacity",
     (datetime.now()-timedelta(hours=2)).isoformat(), 1),
]
cur.executemany(
    "INSERT OR IGNORE INTO alerts VALUES(?,?,?,?,?,?)", alerts
)

freezes = [
    ("frz-001",
     (datetime.now()-timedelta(hours=1)).isoformat(),
     (datetime.now()+timedelta(hours=5)).isoformat(),
     "ap-mumbai-1",
     "Quarter-end freeze — no deployments"),
]
cur.executemany(
    "INSERT OR IGNORE INTO change_freezes VALUES(?,?,?,?,?)", freezes
)

deployments = [
    ("dep-001", "svc-payments", "v2.1.0",
     (datetime.now()-timedelta(hours=3)).isoformat(), "failed"),
    ("dep-002", "svc-payments", "v2.0.9",
     (datetime.now()-timedelta(hours=6)).isoformat(), "success"),
    ("dep-003", "svc-auth", "v1.5.2",
     (datetime.now()-timedelta(days=1)).isoformat(), "success"),
]
cur.executemany(
    "INSERT OR IGNORE INTO deployments VALUES(?,?,?,?,?)", deployments
)

conn.commit()
conn.close()
print("Database seeded successfully: data/incidents.db")