"""Backend functional and security validation. Selenium UI cases live under src/test."""
from .conftest import login


def record(code='ST801'):
    return {'student_code': code, 'student_name': 'QA Test Student', 'course': 'DevOps Lab',
            'attendance_date': '2026-10-21', 'status': 'Present', 'notes': ''}


def test_health_and_seed_data(client):
    assert client.get('/api/health').json()['status'] == 'ok'
    assert login(client).status_code == 303
    payload = client.get('/api/records').json()
    assert payload['total'] == 25
    assert len(payload['items']) == 10
    assert payload['total_pages'] == 3


def test_admin_crud_and_search(client):
    login(client)
    assert client.post('/api/records', json=record()).status_code == 201
    data = client.get('/api/records?q=QA%20Test%20Student').json()
    assert data['total'] == 1
    record_id = data['items'][0]['id']
    edited = record(); edited['student_name'] = 'Updated QA Student'; edited['status'] = 'Late'
    assert client.put(f'/api/records/{record_id}', json=edited).json()['status'] == 'Late'
    assert client.get('/api/records?q=Updated%20QA').json()['total'] == 1
    assert client.delete(f'/api/records/{record_id}').json()['deleted']
    assert client.get('/api/records?q=Updated%20QA').json()['total'] == 0


def test_role_based_page_and_api_protection(client):
    assert client.get('/admin').status_code == 401
    assert login(client, 'student', 'Student@123').status_code == 303
    assert client.get('/admin').status_code == 403
    assert client.get('/api/records').status_code == 200
    assert client.post('/api/records', json=record()).status_code == 403
    assert client.get('/api/export').status_code == 200


def test_invalid_login_and_duplicate(client):
    assert login(client, 'admin', 'wrong').status_code == 401
    login(client)
    assert client.post('/api/records', json=record('ST001')).status_code == 409
    assert client.post('/api/records', json={**record(), 'student_code': 'bad code'}).status_code == 422


def test_csv_import_and_export(client):
    login(client)
    contents = b'student_code,student_name,course,attendance_date,status,notes\nST901,Imported Student,DevOps Lab,2026-10-21,Present,ok\n'
    response = client.post('/api/import', files={'file': ('incoming.csv', contents, 'text/csv')})
    assert response.status_code == 200, response.text
    assert response.json()['imported'] == 1
    report = client.get('/api/export?q=ST901')
    assert report.status_code == 200
    assert 'attachment' in report.headers['content-disposition']
    assert 'ST901,Imported Student' in report.content.decode('utf-8-sig')


def test_csv_import_is_atomic(client):
    login(client)
    csv_bad = b'student_code,student_name,course,attendance_date,status,notes\nST999,Valid Student,DevOps Lab,2026-10-21,Present,ok\nST001,Duplicate Student,DevOps Lab,2026-10-21,Present,duplicate\n'
    result = client.post('/api/import', files={'file': ('bad.csv', csv_bad, 'text/csv')})
    assert result.status_code == 409
    assert client.get('/api/records?q=ST999').json()['total'] == 0


def test_reset_endpoint_requires_secret(client):
    assert client.post('/api/test/reset').status_code == 403
    assert client.post('/api/test/reset', headers={'X-Test-Token': 'test-python-fixture-token'}).status_code == 200


def test_search_is_exactly_filtered(client):
    login(client)
    payload = client.get('/api/records?q=Aarav%20Mehta').json()
    assert payload['total'] == 1
    assert payload['items'][0]['student_code'] == 'ST001'
