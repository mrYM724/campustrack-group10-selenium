"""SQLite persistence and deterministic demonstration data."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / 'data' / 'attendance.db'
DB_PATH = Path(os.environ.get('APP_DB_PATH', str(DEFAULT_DB)))
COURSES = ['Data Structures', 'Computer Networks', 'DevOps Lab', 'Database Systems', 'Python Programming']
NAMES = [
    'Aarav Mehta', 'Sara Khan', 'Riya Nair', 'Kabir Shah', 'Ananya Rao',
    'Vivaan Patel', 'Meera Iyer', 'Ishaan Kulkarni', 'Diya Sharma', 'Arjun Naik',
    'Neha Joshi', 'Zoya Siddiqui', 'Aditya Kumar', 'Tara Desai', 'Om Prakash',
    'Pooja Menon', 'Rohan Das', 'Sana Kapoor', 'Reyansh Verma', 'Ira Malhotra',
    'Mihir Gupta', 'Avni Singh', 'Dev Bhat', 'Nisha Jain', 'Aditi Sethi',
]


def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH), timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA busy_timeout=15000')
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA foreign_keys=ON')
    return con


@contextmanager
def db():
    con = connection()
    try:
        yield con
        con.commit()
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()


def password_hash(password: str, salt: str | None = None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 180_000)
    return f'{salt}${digest.hex()}'


def check_password(password: str, expected: str):
    try:
        salt, digest = expected.split('$', 1)
        found = password_hash(password, salt).split('$', 1)[1]
        return hmac.compare_digest(found, digest)
    except (ValueError, TypeError):
        return False


def initialize():
    with db() as con:
        con.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','user'))
            );
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT NOT NULL UNIQUE,
                student_name TEXT NOT NULL,
                course TEXT NOT NULL,
                attendance_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Present','Absent','Late')),
                notes TEXT NOT NULL DEFAULT ''
            );
        ''')
        count = con.execute('SELECT count(*) FROM users').fetchone()[0]
        if not count:
            con.executemany('INSERT INTO users(username,full_name,password_hash,role) VALUES (?,?,?,?)', [
                ('admin', 'System Administrator', password_hash('Admin@123'), 'admin'),
                ('student', 'Student Viewer', password_hash('Student@123'), 'user'),
            ])
        count = con.execute('SELECT count(*) FROM attendance').fetchone()[0]
        if not count:
            seed_records(con)


def seed_records(con):
    for idx, name in enumerate(NAMES, start=1):
        con.execute('''INSERT INTO attendance(student_code,student_name,course,attendance_date,status,notes)
                       VALUES (?,?,?,?,?,?)''', (
            f'ST{idx:03d}', name, COURSES[(idx - 1) % len(COURSES)],
            f'2026-10-{(idx % 20) + 1:02d}', ['Present','Present','Late','Absent'][idx % 4],
            'Demo attendance record' if idx % 7 == 0 else '',
        ))


def reset_for_tests():
    """Clear only attendance. Preserve existing seeded demo accounts."""
    with db() as con:
        con.execute('DELETE FROM attendance')
        con.execute("DELETE FROM sqlite_sequence WHERE name='attendance'")
        seed_records(con)
