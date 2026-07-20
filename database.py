"""
database.py
Handles all SQLite storage: each visitor's current resume, and a history
of job-description analyses (old score vs new score after rearrange),
scoped per browser session so visitors never see each other's data.
"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "career_agent.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resume (
            session_id TEXT PRIMARY KEY,
            filename TEXT,
            raw_text TEXT,
            structured_json TEXT,
            uploaded_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            jd_text TEXT,
            original_score INTEGER,
            new_score INTEGER,
            missing_keywords TEXT,
            suggestions TEXT,
            tailored_resume_json TEXT,
            cover_letter TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_resume(session_id, filename, raw_text, structured_json):
    conn = get_conn()
    conn.execute("DELETE FROM resume WHERE session_id = ?", (session_id,))
    conn.execute(
        "INSERT INTO resume (session_id, filename, raw_text, structured_json, uploaded_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, filename, raw_text, json.dumps(structured_json), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


def get_resume(session_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM resume WHERE session_id = ?", (session_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "filename": row["filename"],
        "raw_text": row["raw_text"],
        "structured": json.loads(row["structured_json"]),
        "uploaded_at": row["uploaded_at"],
    }


def delete_resume(session_id):
    conn = get_conn()
    conn.execute("DELETE FROM resume WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def save_analysis(session_id, jd_text, original_score, missing_keywords, suggestions):
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO analysis (session_id, jd_text, original_score, missing_keywords, suggestions, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (session_id, jd_text, original_score, json.dumps(missing_keywords), json.dumps(suggestions),
         datetime.utcnow().isoformat())
    )
    conn.commit()
    analysis_id = cur.lastrowid
    conn.close()
    return analysis_id


def update_analysis_tailored(analysis_id, session_id, new_score, tailored_resume_json, cover_letter=None):
    conn = get_conn()
    conn.execute(
        "UPDATE analysis SET new_score = ?, tailored_resume_json = ?, cover_letter = ? WHERE id = ? AND session_id = ?",
        (new_score, json.dumps(tailored_resume_json), cover_letter, analysis_id, session_id)
    )
    conn.commit()
    conn.close()


def get_analysis(analysis_id, session_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM analysis WHERE id = ? AND session_id = ?", (analysis_id, session_id)
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["missing_keywords"] = json.loads(d["missing_keywords"]) if d["missing_keywords"] else []
    d["suggestions"] = json.loads(d["suggestions"]) if d["suggestions"] else []
    d["tailored_resume_json"] = json.loads(d["tailored_resume_json"]) if d["tailored_resume_json"] else None
    return d