import os
from pathlib import Path
from app.database import SQLiteAdapter, DatabaseAdapter
from app.registry import registry

# Instantiate default database adapter (can be overridden dynamically)
DB_PATH = Path(__file__).parent.parent / "data" / "incidents.db"
_default_db: DatabaseAdapter = SQLiteAdapter(str(DB_PATH))

def get_db() -> DatabaseAdapter:
    return _default_db

def set_db(db: DatabaseAdapter):
    global _default_db
    _default_db = db

@registry.register(
    name="check_active_alerts",
    description="Check if there are active alerts for a service",
    parameters={
        "type": "object",
        "properties": {
            "service_id": {
                "type": "string",
                "description": "The service ID to check alerts for"
            }
        },
        "required": ["service_id"]
    }
)
def check_active_alerts(service_id: str) -> dict:
    db = get_db()
    alerts = db.get_active_alerts(service_id)
    return {
        "service_id": service_id,
        "active_alert_count": len(alerts),
        "alerts": alerts
    }

@registry.register(
    name="check_change_freeze",
    description="Check if a change freeze is active for a region",
    parameters={
        "type": "object",
        "properties": {
            "region": {
                "type": "string",
                "description": "The region to check freeze window for"
            }
        },
        "required": ["region"]
    }
)
def check_change_freeze(region: str) -> dict:
    db = get_db()
    freezes = db.get_change_freeze(region)
    return {
        "region": region,
        "freeze_active": len(freezes) > 0,
        "reason": freezes[0]["reason"] if freezes else None
    }

@registry.register(
    name="get_recent_deployments",
    description="Get recent deployment history for a service",
    parameters={
        "type": "object",
        "properties": {
            "service_id": {
                "type": "string",
                "description": "The service ID to get deployment history for"
            }
        },
        "required": ["service_id"]
    }
)
def get_recent_deployments(service_id: str) -> dict:
    db = get_db()
    deployments = db.get_recent_deployments(service_id)
    recent_failures = sum(1 for d in deployments if d["outcome"] == "failed")
    return {
        "service_id": service_id,
        "recent_deployments": deployments,
        "recent_failure_count": recent_failures
    }