# Fix: Login page HTTP 500 with recent FastAPI / Starlette

## Symptom

`GET /login` returns HTTP 500 with `TypeError: cannot use 'tuple' as a dict key (unhashable type: 'dict')`. The original project passed API tests but did not test HTML template rendering.

## Root cause

Modern Starlette interprets `TemplateResponse` arguments as `(request, name, context=...)`. The original app used the obsolete `TemplateResponse('login.html', {'request': request, ...})` positional form. Under Starlette 1.10.0, the dictionary becomes the template name, and Jinja2 cannot use it as a cache key.

## Fix

Changed all four template calls in `app/main.py` to explicit keyword arguments:

```python
return templates.TemplateResponse(request=request, name='login.html', context={'error': False})
```

Similarly updated the unsuccessful-login, authenticated-dashboard and admin-console pages. Added 5 regression tests in `tests/test_template_pages.py`.

## How to start on Windows

1. Stop the old server by pressing Ctrl+C.
2. Extract the fixed ZIP to a new folder (or replace just `app/main.py` in your existing project).
3. Double-click `start_windows.bat` in the project folder.
4. Open http://127.0.0.1:8000 and use `admin` / `Admin@123`.
5. To test backend routes, run `python -m pytest -q tests` with pytest and httpx installed. Selenium tests additionally require Chrome, Maven and Java.

## Validation

13 Python backend/template tests passed with the installed FastAPI/Starlette TestClient. The Java Selenium/Maven suite and GitHub Actions need to be run on Windows/CI.
