import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Protocol, List, Dict, Any

class DatabaseAdapter(Protocol):
    def get_active_alerts(self, service_id: str) -> List[Dict[str, Any]]:
        ...
    def get_change_freeze(self, region: str) -> List[Dict[str, Any]]:
        ...
    def get_recent_deployments(self, service_id: str) -> List[Dict[str, Any]]:
        ...

class SQLiteAdapter:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def get_active_alerts(self, service_id: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT id, type, message, fired_at FROM alerts "
            "WHERE service_id=? AND resolved=0",
            (service_id,)
        ).fetchall()
        conn.close()
        return [
            {"id": r[0], "type": r[1], "message": r[2], "fired_at": r[3]}
            for r in rows
        ]

    def get_change_freeze(self, region: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cur = conn.cursor()
        now = datetime.now().isoformat()
        rows = cur.execute(
            "SELECT id, reason, start_time, end_time FROM change_freezes "
            "WHERE region=? AND start_time<=? AND end_time>=?",
            (region, now, now)
        ).fetchall()
        conn.close()
        return [
            {"id": r[0], "reason": r[1], "start_time": r[2], "end_time": r[3]}
            for r in rows
        ]

    def get_recent_deployments(self, service_id: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT id, version, deployed_at, outcome FROM deployments "
            "WHERE service_id=? ORDER BY deployed_at DESC LIMIT 5",
            (service_id,)
        ).fetchall()
        conn.close()
        return [
            {"id": r[0], "version": r[1], "deployed_at": r[2], "outcome": r[3]}
            for r in rows
        ]
