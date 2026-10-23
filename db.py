import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = "leads.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            location TEXT,
            property_requirement TEXT,
            budget TEXT,
            timeline TEXT,
            message TEXT,
            mobile TEXT,
            email TEXT,
            analysis TEXT,
            score INTEGER,
            tier TEXT,
            urgency TEXT,
            remarks TEXT DEFAULT '',
            anticipation TEXT DEFAULT '',
            synopsis TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Backward-compatible migration for existing local databases.
    lead_columns = {row[1] for row in conn.execute("PRAGMA table_info(leads)").fetchall()}
    if "status" not in lead_columns:
        conn.execute("ALTER TABLE leads ADD COLUMN status TEXT NOT NULL DEFAULT 'Follow Up'")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS follow_ups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            follow_up_date TEXT,
            notes TEXT,
            outcome TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            due_date TEXT,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (list_id) REFERENCES task_lists(id) ON DELETE CASCADE
        )
    """)
    if conn.execute("SELECT COUNT(*) FROM task_lists").fetchone()[0] == 0:
        conn.execute("INSERT INTO task_lists (name) VALUES (?)", ("My tasks",))
    conn.commit()
    conn.close()


def save_lead(lead_data, analysis):
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO leads (
            name, location, property_requirement, budget, timeline, message,
            mobile, email, analysis, score, tier, urgency
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lead_data["name"],
        lead_data["location"],
        lead_data["property_requirement"],
        lead_data["budget"],
        lead_data["timeline"],
        lead_data["message"],
        lead_data.get("mobile", ""),
        lead_data.get("email", ""),
        json.dumps(analysis),
        analysis.get("score", 0),
        analysis.get("tier", "Cold"),
        analysis.get("urgency", "Nurture later"),
    ))
    lead_id = cur.lastrowid
    conn.commit()
    conn.close()
    return lead_id


def update_lead_status(lead_id, status):
    """Persist a lead's sales outcome/status."""
    allowed = {"Follow Up", "Sale Closed", "No Sale Made"}
    if status not in allowed:
        raise ValueError("Invalid lead status")
    conn = get_conn()
    conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
    conn.commit()
    conn.close()


def delete_lead(lead_id):
    """Delete a lead and its follow-up trail."""
    conn = get_conn()
    conn.execute("DELETE FROM follow_ups WHERE lead_id = ?", (lead_id,))
    cur = conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def list_leads():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM leads ORDER BY score DESC, created_at DESC").fetchall()
    conn.close()
    leads = []
    for r in rows:
        d = dict(r)
        d["analysis"] = json.loads(d["analysis"]) if d["analysis"] else {}
        d["follow_up_count"] = get_follow_up_count(d["id"])
        d["next_follow_up"] = get_next_follow_up(d["id"])
        leads.append(d)
    return leads


def get_lead(lead_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["analysis"] = json.loads(d["analysis"]) if d["analysis"] else {}
    d["follow_ups"] = get_follow_ups(lead_id)
    d["follow_up_count"] = len(d["follow_ups"])
    d["next_follow_up"] = get_next_follow_up(lead_id)
    return d


def get_follow_ups(lead_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM follow_ups WHERE lead_id = ? ORDER BY created_at DESC", (lead_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_follow_up_count(lead_id):
    conn = get_conn()
    count = conn.execute(
        "SELECT COUNT(*) FROM follow_ups WHERE lead_id = ?", (lead_id,)
    ).fetchone()[0]
    conn.close()
    return count


def get_next_follow_up(lead_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT follow_up_date FROM follow_ups WHERE lead_id = ? ORDER BY created_at DESC LIMIT 1",
        (lead_id,)
    ).fetchone()
    conn.close()
    return row["follow_up_date"] if row else None


def add_follow_up(lead_id, follow_up_date, notes, outcome):
    conn = get_conn()
    conn.execute(
        "INSERT INTO follow_ups (lead_id, follow_up_date, notes, outcome) VALUES (?, ?, ?, ?)",
        (lead_id, follow_up_date, notes, outcome)
    )
    conn.commit()
    conn.close()


def update_remarks_anticipation(lead_id, remarks, anticipation, synopsis=""):
    conn = get_conn()
    conn.execute(
        "UPDATE leads SET remarks = ?, anticipation = ?, synopsis = ? WHERE id = ?",
        (remarks, anticipation, synopsis, lead_id)
    )
    conn.commit()
    conn.close()


def is_due_soon(date_str):
    if not date_str:
        return None
    try:
        # accept YYYY-MM-DD or simple strings
        if len(date_str) == 10 and date_str[4] == "-":
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            return None
        today = datetime.now().date()
        if d == today:
            return "today"
        if d == today + timedelta(days=1):
            return "tomorrow"
        if d < today:
            return "overdue"
    except:
        pass
    return None


def list_task_lists():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM task_lists ORDER BY created_at, name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_task_list(name):
    conn = get_conn()
    cur = conn.execute("INSERT OR IGNORE INTO task_lists (name) VALUES (?)", (name.strip(),))
    row = conn.execute("SELECT id FROM task_lists WHERE name = ?", (name.strip(),)).fetchone()
    conn.commit()
    conn.close()
    return row["id"] if row else cur.lastrowid


def delete_task_list(list_id):
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE list_id = ?", (list_id,))
    conn.execute("DELETE FROM task_lists WHERE id = ?", (list_id,))
    conn.commit()
    conn.close()


def list_tasks(list_id=None):
    conn = get_conn()
    if list_id is None:
        rows = conn.execute("SELECT tasks.*, task_lists.name AS list_name FROM tasks JOIN task_lists ON task_lists.id = tasks.list_id ORDER BY completed, due_date IS NULL, due_date, created_at DESC").fetchall()
    else:
        rows = conn.execute("SELECT tasks.*, task_lists.name AS list_name FROM tasks JOIN task_lists ON task_lists.id = tasks.list_id WHERE list_id = ? ORDER BY completed, due_date IS NULL, due_date, created_at DESC", (list_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_task(list_id, title, due_date=None):
    conn = get_conn()
    cur = conn.execute("INSERT INTO tasks (list_id, title, due_date) VALUES (?, ?, ?)", (list_id, title.strip(), due_date or None))
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return task_id


def toggle_task(task_id, completed):
    conn = get_conn()
    conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (1 if completed else 0, task_id))
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def rescore_existing_leads():
    """Recalculate score/tier for every saved lead without making any AI API calls.

    The qualitative AI analysis is preserved; only score, tier, reason and urgency
    are recalculated using the deterministic scoring rubric.
    """
    from scoring import score_lead

    conn = get_conn()
    rows = conn.execute("SELECT * FROM leads").fetchall()
    updated = 0
    for row in rows:
        lead = dict(row)
        try:
            analysis = json.loads(lead.get("analysis") or "{}")
        except (json.JSONDecodeError, TypeError):
            analysis = {}
        scored = score_lead(lead, analysis)
        analysis.update(scored)
        conn.execute(
            "UPDATE leads SET analysis = ?, score = ?, tier = ?, urgency = ? WHERE id = ?",
            (json.dumps(analysis), scored["score"], scored["tier"], scored["urgency"], lead["id"]),
        )
        updated += 1
    conn.commit()
    conn.close()
    return updated
