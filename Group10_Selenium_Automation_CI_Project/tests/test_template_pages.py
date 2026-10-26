"""Regression checks for actual HTML pages and supported TemplateResponse signatures.

The original release passed API tests but crashed when visiting /login under
newer FastAPI/Starlette due to obsolete TemplateResponse positional arguments.
"""
from .conftest import login


def test_login_page_renders(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert 'Choose your portal' in response.text
    assert 'admin-portal-link' in response.text
    assert 'student-portal-link' in response.text
    assert 'login-form' not in response.text
    for route, label in [('/admin/login', 'Administrator sign in'), ('/student/login', 'Student sign in')]:
        portal = client.get(route)
        assert portal.status_code == 200
        assert label in portal.text
        assert 'login-form' in portal.text
    admin_page = client.get('/admin/login').text
    student_page = client.get('/student/login').text
    assert 'student / Student@123' not in admin_page
    assert 'admin / Admin@123' not in student_page


def test_bad_password_renders_login_error(client):
    response = login(client, 'admin', 'incorrect')
    assert response.status_code == 401
    assert 'Invalid username or password' in response.text


def test_admin_page_and_dashboard_render(client):
    assert client.get('/', follow_redirects=False).status_code == 303
    assert login(client).status_code == 303
    dashboard = client.get('/')
    assert dashboard.status_code == 200
    assert 'Attendance overview' in dashboard.text
    assert 'admin-nav' in dashboard.text
    admin = client.get('/admin')
    assert admin.status_code == 200
    assert 'Admin console' in admin.text
    assert 'Access granted' in admin.text


def test_user_page_renders_without_admin_controls(client):
    assert login(client, 'student', 'Student@123').status_code == 303
    dashboard = client.get('/student')
    assert dashboard.status_code == 200
    assert 'Student attendance portal' in dashboard.text
    assert 'View-only access' in dashboard.text
    assert 'admin-nav' not in dashboard.text
    assert client.get('/admin').status_code == 403


def test_static_resources_load(client):
    for resource, expected in [('/static/style.css', '--teal'),
                               ('/static/app.js', 'search-input')]:
        response = client.get(resource)
        assert response.status_code == 200
        assert expected in response.text


def test_separate_login_portals_enforce_the_role(client):
    # An administrator's valid credentials must NOT enter the student portal.
    wrong_portal = client.post('/student/login', data={'username': 'admin', 'password': 'Admin@123'})
    assert wrong_portal.status_code == 401
    assert 'Student sign in' in wrong_portal.text
    # Equally, student credentials cannot be used on the admin login page.
    wrong_portal = client.post('/admin/login', data={'username': 'student', 'password': 'Student@123'})
    assert wrong_portal.status_code == 401
    assert 'Administrator sign in' in wrong_portal.text
    # Old combined POST /login must not authenticate either role.
    assert client.post('/login', data={'username': 'admin', 'password': 'Admin@123'}).status_code == 405
    assert client.get('/', follow_redirects=False).status_code == 303
    response = client.post('/student/login', data={'username': 'student', 'password': 'Student@123'}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers['location'] == '/student'
    assert client.get('/', follow_redirects=False).headers['location'] == '/student'
    assert client.get('/admin').status_code == 403
    assert client.get('/student').status_code == 200
