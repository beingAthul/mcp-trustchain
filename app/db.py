import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'trustchain.db')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tool Registry Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tools (
            tool_id TEXT PRIMARY KEY,
            name TEXT,
            status TEXT,
            severity TEXT,
            approved_hash TEXT,
            last_verified TEXT
        )
    ''')
    # Audit Log Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            action TEXT,
            result TEXT,
            reason TEXT,
            tool_id TEXT
        )
    ''')
    # Tool Versions Table (for rollback)
    c.execute('''
        CREATE TABLE IF NOT EXISTS tool_versions (
            version_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id TEXT,
            config_snapshot TEXT,
            hash TEXT,
            timestamp TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def register_tool(tool_id: str, name: str, status: str, severity: str, approved_hash: str = None):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    # Upsert
    c.execute('''
        INSERT INTO tools (tool_id, name, status, severity, approved_hash, last_verified)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(tool_id) DO UPDATE SET
            status=excluded.status,
            severity=excluded.severity,
            approved_hash=excluded.approved_hash,
            last_verified=excluded.last_verified
    ''', (tool_id, name, status, severity, approved_hash, now))
    conn.commit()
    conn.close()

def save_tool_version(tool_id: str, config_snapshot: str, hash: str, status: str):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute('''
        INSERT INTO tool_versions (tool_id, config_snapshot, hash, timestamp, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (tool_id, config_snapshot, hash, now, status))
    conn.commit()
    conn.close()

def get_last_approved_version(tool_id: str) -> Dict[str, Any]:
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM tool_versions 
        WHERE tool_id = ? AND status = 'APPROVED' 
        ORDER BY timestamp DESC LIMIT 1
    ''', (tool_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_tools() -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tools ORDER BY last_verified DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_tool(tool_id: str) -> Dict[str, Any]:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tools WHERE tool_id = ?', (tool_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def log_audit(action: str, result: str, reason: str, tool_id: str = None):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute('''
        INSERT INTO audits (timestamp, action, result, reason, tool_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (now, action, result, reason, tool_id))
    conn.commit()
    conn.close()

def get_audits() -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM audits ORDER BY timestamp DESC LIMIT 100')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_dashboard_metrics() -> Dict[str, Any]:
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) as total FROM tools')
    total_tools = c.fetchone()['total']
    
    c.execute("SELECT COUNT(*) as approved FROM tools WHERE status='APPROVED' OR status='RE-APPROVED'")
    approved_tools = c.fetchone()['approved']
    
    c.execute("SELECT COUNT(*) as blocked FROM tools WHERE status='BLOCKED'")
    blocked_tools = c.fetchone()['blocked']
    
    c.execute("SELECT COUNT(*) as violations FROM audits WHERE result='BLOCK' AND action='VERIFY'")
    integrity_violations = c.fetchone()['violations']
    
    conn.close()
    
    return {
        "total_tools": total_tools,
        "approved_tools": approved_tools,
        "blocked_tools": blocked_tools,
        "integrity_violations": integrity_violations
    }

# Initialize the db when module is loaded
init_db()
