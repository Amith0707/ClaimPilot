import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "claimbot"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            id SERIAL PRIMARY KEY,
            claim_text TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            assigned_team TEXT NOT NULL,
            reasoning TEXT NOT NULL,
            confidence TEXT NOT NULL,
            elapsed_ms INTEGER,
            source TEXT NOT NULL DEFAULT 'single',
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_claim(claim_text, result, elapsed_ms, source="single"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO claims (claim_text, category, priority, assigned_team, reasoning, confidence, elapsed_ms, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        claim_text, result["category"], result["priority"],
        result["assigned_team"], result["reasoning"], result["confidence"],
        elapsed_ms, source
    ))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_id

def get_all_claims(limit=100):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM claims ORDER BY created_at DESC LIMIT %s;", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows