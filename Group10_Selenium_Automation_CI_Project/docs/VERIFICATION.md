# Verification and Testing Status

This document distinguishes the actual checks performed while preparing this ZIP from tests that must run on the user's Windows laptop or GitHub Actions environment.

**Confirmed:** Python application/API checks run with pytest and FastAPI's TestClient; see `tests/test_api.py` for runnable assertions. These cover authentication, authorization, CRUD, pagination API, search, CSV import/export, rejection of invalid data, test reset security and health. Python syntax compilation, YAML parsing and JavaScript syntax inspection may also be performed during packaging.

**Not claimed:** Java Selenium/TestNG browser tests have not been executed with Maven in the packaging environment because Maven artifacts cannot be downloaded there. A real GitHub Actions green or red CI run has not been produced on your repository. Run `mvn clean test` locally and push to GitHub to verify the complete mandated Selenium -> TestNG -> ExtentReports -> GitHub Actions flow.

**Verification commands:**

```sh
python -m pytest -q tests
python -m compileall -q app tests scripts
mvn clean test -Dheadless=true
```

The last command needs the web application running with `TEST_MODE=1`, a matching `TEST_TOKEN`, installed Chrome, Java 17+ and Maven.

## Update: HTML template regression fix (2026-10-26)

After fixing `TemplateResponse` in `app/main.py`, 13 Python tests passed, including 5 new HTML rendering tests covering `/login`, invalid login, admin and user dashboards, and static assets. Tests were executed with FastAPI 0.128.2 / Starlette 0.50.0 available in the verification environment. The reported Windows crash occurred on FastAPI 0.162.0 / Starlette 1.10.0; the replacement keyword-call interface is compatible with their documented request-first API. A full Java Selenium/CI run is still to be verified in the user's environment.
