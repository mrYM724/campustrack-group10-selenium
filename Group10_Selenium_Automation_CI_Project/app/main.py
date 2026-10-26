"""Attendance Management System: admin CRUD, viewer role, CSV import/export.

All mutating API routes are server-side role protected. TEST_MODE is explicitly
opt-in and the test-reset route is disabled in normal deployments.
"""
from __future__ import annotations

import csv
import io
import os
import re
import sqlite3
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Form, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.sessions import SessionMiddleware

from .config import SEARCH_BUG_ENABLED
from .db import DB_PATH, check_password, db, initialize, reset_for_tests

ROOT = Path(__file__).resolve().parent
app = FastAPI(title='CampusTrack Attendance Management', docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware,
                   secret_key=os.environ.get('SESSION_SECRET', 'local-demo-replace-for-production-98x'),
                   same_site='lax', https_only=False, max_age=3600 * 8)
app.mount('/static', StaticFiles(directory=str(ROOT / 'static')), name='static')
templates = Jinja2Templates(directory=str(ROOT / 'templates'))


@app.on_event('startup')
def setup():
    initialize()


def current_user(request: Request):
    user = request.session.get('user')
    return user if isinstance(user, dict) and user.get('role') in ('admin', 'user') else None


def require_user(request: Request):
    user = current_user(request)
    if not user:
        raise HTTPException(401, 'Login required')
    return user


def require_admin(request: Request):
    user = require_user(request)
    if user['role'] != 'admin':
        raise HTTPException(403, 'Admin role required')
    return user


@app.get('/api/health')
def health():
    return {'status': 'ok', 'app': 'CampusTrack'}


def role_destination(user: dict) -> str:
    return '/' if user['role'] == 'admin' else '/student'


@app.get('/login', response_class=HTMLResponse)
def choose_login_portal(request: Request):
    """Public role selection — no combined admin/student credential form."""
    user = current_user(request)
    if user:
        return RedirectResponse(role_destination(user), status_code=303)
    return templates.TemplateResponse(request=request, name='portal.html', context={})


def render_role_login(request: Request, role: str, error: bool = False, status_code: int = 200):
    return templates.TemplateResponse(
        request=request,
        name='login.html',
        context={'error': error, 'role': role, 'role_label': 'Administrator' if role == 'admin' else 'Student'},
        status_code=status_code,
    )


@app.get('/admin/login', response_class=HTMLResponse)
def admin_login_screen(request: Request):
    user = current_user(request)
    if user:
        return RedirectResponse(role_destination(user), status_code=303)
    return render_role_login(request, 'admin')


@app.get('/student/login', response_class=HTMLResponse)
def student_login_screen(request: Request):
    user = current_user(request)
    if user:
        return RedirectResponse(role_destination(user), status_code=303)
    return render_role_login(request, 'user')


def perform_role_login(request: Request, role: str, username: str, password: str):
    with db() as con:
        row = con.execute('SELECT * FROM users WHERE username=?', (username.strip(),)).fetchone()
    # Authenticate BOTH password and role. Correct credentials cannot log into the wrong portal.
    if not row or not check_password(password, row['password_hash']) or row['role'] != role:
        return render_role_login(request, role, error=True, status_code=401)
    request.session.clear()
    request.session['user'] = {'username': row['username'], 'name': row['full_name'], 'role': row['role']}
    return RedirectResponse(role_destination(request.session['user']), status_code=303)


@app.post('/admin/login')
def admin_log_in(request: Request, username: str = Form(...), password: str = Form(...)):
    return perform_role_login(request, 'admin', username, password)


@app.post('/student/login')
def student_log_in(request: Request, username: str = Form(...), password: str = Form(...)):
    return perform_role_login(request, 'user', username, password)


@app.post('/logout')
def log_out(request: Request):
    request.session.clear()
    return RedirectResponse('/login', status_code=303)


@app.get('/', response_class=HTMLResponse)
def dashboard(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse('/login', status_code=303)
    if user['role'] != 'admin':
        return RedirectResponse('/student', status_code=303)
    return templates.TemplateResponse(request=request, name='dashboard.html', context={'user': user})


@app.get('/student', response_class=HTMLResponse)
def student_dashboard(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse('/student/login', status_code=303)
    if user['role'] != 'user':
        raise HTTPException(403, 'Student role required')
    return templates.TemplateResponse(request=request, name='dashboard.html', context={'user': user})


@app.get('/admin', response_class=HTMLResponse)
def admin_only_page(request: Request):
    user = require_admin(request)
    return templates.TemplateResponse(request=request, name='admin.html', context={'user': user})


@app.get('/api/me')
def me(request: Request):
    return require_user(request)


class Record(BaseModel):
    student_code: str = Field(min_length=2, max_length=20)
    student_name: str = Field(min_length=2, max_length=80)
    course: str = Field(min_length=2, max_length=80)
    attendance_date: date
    status: Literal['Present', 'Absent', 'Late']
    notes: str = Field(default='', max_length=250)

    @field_validator('student_code')
    @classmethod
    def validate_code(cls, value):
        v = value.strip().upper()
        if not re.fullmatch(r'[A-Z0-9-]{2,20}', v):
            raise ValueError('Student code must contain only letters, numbers, or hyphens')
        return v

    @field_validator('student_name', 'course')
    @classmethod
    def strip_text(cls, value):
        result = value.strip()
        if len(result) < 2:
            raise ValueError('Field is too short')
        return result


def record_dict(record: Record):
    data = record.model_dump()
    data['attendance_date'] = record.attendance_date.isoformat()
    return data


@app.get('/api/records')
def list_records(request: Request,
                 q: str = Query('', max_length=100),
                 page: int = Query(1, ge=1),
                 per_page: int = Query(10, ge=1, le=50)):
    require_user(request)
    # The one-line condition is intentionally switchable for the required CI regression demo.
    query = '' if SEARCH_BUG_ENABLED else q.strip()
    filters = []
    values = []
    if query:
        filters.append('(student_code LIKE ? OR student_name LIKE ? OR course LIKE ? OR status LIKE ?)')
        values.extend([f'%{query}%'] * 4)
    where = f"WHERE {' AND '.join(filters)}" if filters else ''
    with db() as con:
        total = con.execute(f'SELECT COUNT(*) FROM attendance {where}', values).fetchone()[0]
        rows = con.execute(f'SELECT * FROM attendance {where} ORDER BY id ASC LIMIT ? OFFSET ?',
                           [*values, per_page, (page - 1) * per_page]).fetchall()
    return {'items': [dict(x) for x in rows], 'total': total, 'page': page,
            'per_page': per_page, 'total_pages': max(1, (total + per_page - 1) // per_page)}


@app.get('/api/stats')
def stats(request: Request):
    require_user(request)
    with db() as con:
        total = con.execute('SELECT COUNT(*) FROM attendance').fetchone()[0]
        present = con.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'").fetchone()[0]
        absent = con.execute("SELECT COUNT(*) FROM attendance WHERE status='Absent'").fetchone()[0]
        late = con.execute("SELECT COUNT(*) FROM attendance WHERE status='Late'").fetchone()[0]
        students = con.execute('SELECT COUNT(DISTINCT student_code) FROM attendance').fetchone()[0]
    return {'total': total, 'present': present, 'absent': absent, 'late': late, 'students': students}


@app.post('/api/records', status_code=201)
def create_record(request: Request, record: Record):
    require_admin(request)
    fields = record_dict(record)
    try:
        with db() as con:
            cur = con.execute('''INSERT INTO attendance(student_code,student_name,course,attendance_date,status,notes)
                                 VALUES (:student_code,:student_name,:course,:attendance_date,:status,:notes)''', fields)
            fields['id'] = cur.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'Student code already exists')
    return fields


@app.put('/api/records/{record_id}')
def update_record(request: Request, record_id: int, record: Record):
    require_admin(request)
    values = record_dict(record)
    values['id'] = record_id
    try:
        with db() as con:
            cur = con.execute('''UPDATE attendance SET student_code=:student_code,
                    student_name=:student_name, course=:course, attendance_date=:attendance_date,
                    status=:status, notes=:notes WHERE id=:id''', values)
            if cur.rowcount == 0:
                raise HTTPException(404, 'Record not found')
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'Student code already exists')
    return values


@app.delete('/api/records/{record_id}')
def delete_record(request: Request, record_id: int):
    require_admin(request)
    with db() as con:
        cur = con.execute('DELETE FROM attendance WHERE id=?', (record_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, 'Record not found')
    return {'deleted': True, 'id': record_id}


COLS = ['student_code', 'student_name', 'course', 'attendance_date', 'status', 'notes']


def safe_csv_value(value):
    """Prevent spreadsheet formula execution when downloading user-controlled fields."""
    s = str(value or '')
    if s.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + s
    return s


@app.get('/api/export')
def export_records(request: Request, q: str = Query('', max_length=100)):
    require_user(request)
    query = q.strip()
    args = [f'%{query}%'] * 4 if query else []
    where = 'WHERE student_code LIKE ? OR student_name LIKE ? OR course LIKE ? OR status LIKE ?' if query else ''
    with db() as con:
        rows = con.execute(f'SELECT * FROM attendance {where} ORDER BY id ASC', args).fetchall()
    buff = io.StringIO(newline='')
    writer = csv.writer(buff)
    writer.writerow(COLS)
    for item in rows:
        writer.writerow([safe_csv_value(item[col]) for col in COLS])
    return StreamingResponse(iter([buff.getvalue().encode('utf-8-sig')]), media_type='text/csv; charset=utf-8',
                             headers={'Content-Disposition': 'attachment; filename="attendance_report.csv"',
                                      'Cache-Control': 'no-store'})


@app.post('/api/import')
async def import_records(request: Request, file: UploadFile = File(...)):
    require_admin(request)
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(400, 'Please select a CSV file')
    data = await file.read(512 * 1024 + 1)
    if len(data) > 512 * 1024:
        raise HTTPException(413, 'CSV exceeds 512 KB limit')
    try:
        text = data.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None or not set(COLS[:-1]).issubset(set(reader.fieldnames)):
            raise HTTPException(400, 'Missing required CSV columns')
        parsed = []
        for index, row in enumerate(reader, start=2):
            if index > 502:
                raise HTTPException(413, 'Maximum 500 CSV records per upload')
            try:
                parsed.append(record_dict(Record(**{key: row.get(key, '') for key in COLS})))
            except Exception as exc:
                raise HTTPException(400, f'Invalid data on CSV line {index}: {exc}')
        if not parsed:
            raise HTTPException(400, 'CSV has no records')
    except UnicodeDecodeError:
        raise HTTPException(400, 'CSV must be UTF-8 encoded')
    try:
        with db() as con:
            con.executemany('''INSERT INTO attendance(student_code,student_name,course,attendance_date,status,notes)
                               VALUES (:student_code,:student_name,:course,:attendance_date,:status,:notes)''', parsed)
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'CSV contains a duplicate student code')
    return {'imported': len(parsed), 'message': f'Imported {len(parsed)} attendance records'}


@app.post('/api/test/reset')
def test_reset(request: Request):
    if os.environ.get('TEST_MODE') != '1':
        raise HTTPException(404, 'Not found')
    token = os.environ.get('TEST_TOKEN', '')
    if not token or request.headers.get('X-Test-Token') != token:
        raise HTTPException(403, 'Invalid test token')
    reset_for_tests()
    return {'reset': True, 'records': 25}
