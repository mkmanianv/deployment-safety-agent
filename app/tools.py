import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "incidents.db"

def get_db():
    return sqlite3.connect(str(DB_PATH))

def check_active_alerts(service_id: str) -> dict:
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, type, message, fired_at FROM alerts "
        "WHERE service_id=? AND resolved=0",
        (service_id,)
    ).fetchall()
    conn.close()
    alerts = [
        {"id": r[0], "type": r[1], "message": r[2], "fired_at": r[3]}
        for r in rows
    ]
    return {
        "service_id": service_id,
        "active_alert_count": len(alerts),
        "alerts": alerts
    }

def check_change_freeze(region: str) -> dict:
    conn = get_db()
    cur = conn.cursor()
    now = datetime.now().isoformat()
    rows = cur.execute(
        "SELECT id, reason, start_time, end_time FROM change_freezes "
        "WHERE region=? AND start_time<=? AND end_time>=?",
        (region, now, now)
    ).fetchall()
    conn.close()
    return {
        "region": region,
        "freeze_active": len(rows) > 0,
        "reason": rows[0][1] if rows else None
    }

def get_recent_deployments(service_id: str) -> dict:
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, version, deployed_at, outcome FROM deployments "
        "WHERE service_id=? ORDER BY deployed_at DESC LIMIT 5",
        (service_id,)
    ).fetchall()
    conn.close()
    deployments = [
        {"id": r[0], "version": r[1], "deployed_at": r[2], "outcome": r[3]}
        for r in rows
    ]
    recent_failures = sum(1 for d in deployments if d["outcome"] == "failed")
    return {
        "service_id": service_id,
        "recent_deployments": deployments,
        "recent_failure_count": recent_failures
    }