"""
v5 Audit Logger — Comprehensive SQLite + Markdown audit trail.
Logs every agent action, conflict, resolution, and state change.
"""

import sqlite3
import os
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class AuditLogger:
    """Logs every agent action, conflict, resolution, and state change."""

    def __init__(self, db_path: str = "./database/audit.db", log_dir: str = "./uploads/logs"):
        self.db_path = db_path
        self.log_dir = log_dir
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                agent TEXT NOT NULL,
                role TEXT,
                action TEXT NOT NULL,
                state TEXT,
                content TEXT,
                metadata TEXT,
                severity TEXT DEFAULT 'INFO'
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                round INTEGER,
                topic TEXT,
                agents_involved TEXT,
                disagreement TEXT,
                resolution TEXT,
                resolution_agent TEXT
            )
        """)
        conn.commit()
        conn.close()

    def log(self, project_id: str, agent: str, action: str, role: str = "",
            state: str = "", content: str = "", metadata: Optional[Dict] = None,
            severity: str = "INFO"):
        ts = time.time()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO audit (project_id, timestamp, agent, role, action, state, content, metadata, severity) VALUES (?,?,?,?,?,?,?,?,?)",
            (project_id, ts, agent, role, action, state, content[:5000], json.dumps(metadata or {}), severity)
        )
        conn.commit()
        conn.close()
        self._append_md(project_id, ts, agent, role, action, state, content, metadata, severity)

    def log_conflict(self, project_id: str, round_num: int, topic: str,
                     agents_involved: List[str], disagreement: str,
                     resolution: str = "", resolution_agent: str = ""):
        ts = time.time()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO conflicts (project_id, timestamp, round, topic, agents_involved, disagreement, resolution, resolution_agent) VALUES (?,?,?,?,?,?,?,?)",
            (project_id, ts, round_num, topic, json.dumps(agents_involved), disagreement, resolution, resolution_agent)
        )
        conn.commit()
        conn.close()
        self._append_md(
            project_id, ts, "CONFLICT", "ConflictResolutionAgent",
            f"DEBATE ROUND {round_num}: {topic}", "CONFLICT",
            f"Agents: {', '.join(agents_involved)}\nDisagreement: {disagreement}\nResolution: {resolution or 'PENDING'}",
            {}, "CONFLICT"
        )

    def _append_md(self, project_id: str, ts: float, agent: str, role: str,
                   action: str, state: str, content: str, metadata: Dict, severity: str):
        md_path = os.path.join(self.log_dir, f"{project_id}_audit.md")
        dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        with open(md_path, "a", encoding="utf-8") as f:
            f.write(f"\n---\n\n")
            f.write(f"**Timestamp:** {dt}  \n")
            f.write(f"**Severity:** `{severity}`  \n")
            f.write(f"**Agent:** `{agent}`  \n")
            f.write(f"**Role:** `{role}`  \n")
            f.write(f"**Action:** {action}  \n")
            f.write(f"**State:** `{state}`  \n")
            if metadata:
                f.write(f"**Metadata:**\n```json\n{json.dumps(metadata, indent=2)}\n```\n")
            f.write(f"\n### Content\n\n{content}\n\n")

    def export_full_md(self, project_id: str, memory_text: str) -> str:
        """Export a consolidated Markdown audit log for a project."""
        md_path = os.path.join(self.log_dir, f"{project_id}_COMPLETE.md")
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Full Audit Log: {project_id}\n\n")
            f.write(f"Generated: {dt}\n\n")
            f.write("## Complete Memory & Process Dump\n\n")
            f.write(f"```\n{memory_text}\n```\n\n")
            f.write("## Structured Audit Entries\n\n")
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                "SELECT timestamp, agent, role, action, state, severity, content, metadata FROM audit WHERE project_id = ? ORDER BY timestamp",
                (project_id,)
            )
            for row in c.fetchall():
                ts, agent, role, action, state, sev, content, meta = row
                tstr = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"### {tstr} | {agent} | {action} | `{sev}`\n\n")
                f.write(f"- **Role:** {role}\n")
                f.write(f"- **State:** {state}\n")
                f.write(f"- **Content:** {content}\n")
                f.write(f"- **Metadata:** {meta}\n\n")
            conn.close()
            f.write("\n---\n\n*End of Audit Log*\n")
        return md_path

    def get_project_logs(self, project_id: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT * FROM audit WHERE project_id = ? ORDER BY timestamp",
            (project_id,)
        )
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
