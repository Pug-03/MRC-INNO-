import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, date
from typing import Iterator

from .config import DB_PATH

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS detections (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT    NOT NULL,
    day        TEXT    NOT NULL,
    category   TEXT    NOT NULL,
    color_name TEXT    NOT NULL,
    hue        INTEGER,
    saturation INTEGER,
    value      INTEGER
);
CREATE INDEX IF NOT EXISTS idx_detections_day      ON detections(day);
CREATE INDEX IF NOT EXISTS idx_detections_category ON detections(category);
CREATE INDEX IF NOT EXISTS idx_detections_ts       ON detections(ts);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


_conn = _connect()
with _lock:
    _conn.executescript(SCHEMA)
    _conn.commit()


@contextmanager
def cursor() -> Iterator[sqlite3.Cursor]:
    with _lock:
        cur = _conn.cursor()
        try:
            yield cur
            _conn.commit()
        finally:
            cur.close()


def insert_detection(category: str, color_name: str, h: int, s: int, v: int) -> dict:
    now = datetime.now()
    with cursor() as cur:
        cur.execute(
            "INSERT INTO detections (ts, day, category, color_name, hue, saturation, value) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (now.isoformat(timespec="seconds"), now.date().isoformat(), category, color_name, h, s, v),
        )
        row_id = cur.lastrowid
    return {
        "id": row_id,
        "ts": now.isoformat(timespec="seconds"),
        "day": now.date().isoformat(),
        "category": category,
        "color_name": color_name,
    }


def totals_today() -> dict:
    today = date.today().isoformat()
    return totals_for_day(today)


def totals_for_day(day: str) -> dict:
    out = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    with cursor() as cur:
        cur.execute(
            "SELECT category, COUNT(*) AS n FROM detections WHERE day=? GROUP BY category",
            (day,),
        )
        for row in cur.fetchall():
            out[row["category"]] = row["n"]
    out["total"] = sum(out[k] for k in ("A", "B", "C", "D", "E"))
    out["day"] = day
    return out


def totals_range(start: str, end: str) -> list[dict]:
    with cursor() as cur:
        cur.execute(
            "SELECT day, category, COUNT(*) AS n FROM detections "
            "WHERE day BETWEEN ? AND ? GROUP BY day, category ORDER BY day",
            (start, end),
        )
        rows = cur.fetchall()
    days: dict[str, dict] = {}
    for r in rows:
        d = days.setdefault(r["day"], {"day": r["day"], "A": 0, "B": 0, "C": 0, "D": 0, "E": 0})
        d[r["category"]] = r["n"]
    for d in days.values():
        d["total"] = d["A"] + d["B"] + d["C"] + d["D"] + d["E"]
    return sorted(days.values(), key=lambda x: x["day"])


def recent_events(limit: int = 50) -> list[dict]:
    with cursor() as cur:
        cur.execute(
            "SELECT id, ts, category, color_name FROM detections ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]


def clear_all() -> int:
    with cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM detections")
        n = cur.fetchone()[0]
        cur.execute("DELETE FROM detections")
        cur.execute("DELETE FROM sqlite_sequence WHERE name='detections'")
    return n


def clear_day(day: str) -> int:
    with cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM detections WHERE day=?", (day,))
        n = cur.fetchone()[0]
        cur.execute("DELETE FROM detections WHERE day=?", (day,))
    return n


def all_in_range(start: str, end: str) -> list[dict]:
    with cursor() as cur:
        cur.execute(
            "SELECT id, ts, day, category, color_name, hue, saturation, value "
            "FROM detections WHERE day BETWEEN ? AND ? ORDER BY ts",
            (start, end),
        )
        return [dict(r) for r in cur.fetchall()]
