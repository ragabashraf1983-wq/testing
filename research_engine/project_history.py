"""
v5 Project History — SQLite persistence for continuation, forking, and referencing.
"""

import sqlite3
import json
import os
import time
import uuid
from typing import Dict, Any, List, Optional


class ProjectHistory:
    """Manages persistent project storage with versioning and continuation."""

    def __init__(self, db_path: str = "./database/projects.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                topic TEXT NOT NULL,
                created_at REAL,
                updated_at REAL,
                status TEXT,
                current_state TEXT,
                draft_iteration INTEGER,
                peer_review_round INTEGER,
                snapshot TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                version_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                created_at REAL,
                label TEXT,
                snapshot TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS references_table (
                ref_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_project_id TEXT,
                target_project_id TEXT,
                relation TEXT,
                created_at REAL
            )
        """)
        conn.commit()
        conn.close()

    def save_project(self, project_id: str, title: str, topic: str, status: str,
                     current_state: str, draft_iteration: int, peer_review_round: int,
                     snapshot: Dict[str, Any]):
        now = time.time()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO projects (project_id, title, topic, created_at, updated_at, status, current_state, draft_iteration, peer_review_round, snapshot)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                title=excluded.title,
                topic=excluded.topic,
                updated_at=excluded.updated_at,
                status=excluded.status,
                current_state=excluded.current_state,
                draft_iteration=excluded.draft_iteration,
                peer_review_round=excluded.peer_review_round,
                snapshot=excluded.snapshot
        """, (project_id, title, topic, now, now, status, current_state, draft_iteration, peer_review_round, json.dumps(snapshot)))
        conn.commit()
        conn.close()

    def create_version(self, project_id: str, label: str, snapshot: Dict[str, Any]) -> str:
        version_id = f"{project_id}_v{int(time.time())}"
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO versions (version_id, project_id, created_at, label, snapshot) VALUES (?,?,?,?,?)",
            (version_id, project_id, time.time(), label, json.dumps(snapshot))
        )
        conn.commit()
        conn.close()
        return version_id

    def load_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
        row = c.fetchone()
        conn.close()
        if row:
            data = dict(row)
            data["snapshot"] = json.loads(data["snapshot"])
            return data
        return None

    def list_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if status:
            c.execute("SELECT project_id, title, topic, status, updated_at, current_state FROM projects WHERE status = ? ORDER BY updated_at DESC", (status,))
        else:
            c.execute("SELECT project_id, title, topic, status, updated_at, current_state FROM projects ORDER BY updated_at DESC")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def add_reference(self, source_project_id: str, target_project_id: str, relation: str = "continues"):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO references_table (source_project_id, target_project_id, relation, created_at) VALUES (?,?,?,?)",
            (source_project_id, target_project_id, relation, time.time())
        )
        conn.commit()
        conn.close()

    def get_references(self, project_id: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT * FROM references_table WHERE source_project_id = ? OR target_project_id = ?",
            (project_id, project_id)
        )
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def fork_project(self, original_project_id: str, new_title: str) -> Optional[Dict[str, Any]]:
        original = self.load_project(original_project_id)
        if not original:
            return None
        snapshot = original["snapshot"]
        new_id = f"{original_project_id}_fork_{uuid.uuid4().hex[:6]}"
        self.save_project(
            project_id=new_id,
            title=new_title,
            topic=snapshot.get("topic", original["topic"]),
            status="forked",
            current_state="INIT",
            draft_iteration=0,
            peer_review_round=0,
            snapshot=snapshot,
        )
        self.add_reference(new_id, original_project_id, "forked_from")
        return self.load_project(new_id)
