## Windows login page fix (26 October 2026)

This package preserves the earlier fix for the HTTP 500 error on `/login` with recent FastAPI/Starlette versions (including the versions shown in the Windows startup log). All HTML pages now use `TemplateResponse(request=request, name=..., context=...)` rather than the obsolete positional form. Added `tests/test_template_pages.py` to catch the same issue in future.

**If you have the previous version running:** press `Ctrl+C` in its server window, extract **this fixed ZIP** to a new folder, double-click `start_windows.bat`, and open http://127.0.0.1:8000. The new Group No. 10 folder includes the updated `app/main.py` and all automated testing files.

# CampusTrack | Group No. 10 — Selenium Automation + CI/CD

**Project title:** Automated Functional & Regression Testing of an Attendance Management System Using Selenium WebDriver, TestNG, Maven, ExtentReports and GitHub Actions.

This is a **complete educational QA mini project**, with (1) a working attendance-management website and (2) a separate Java browser-automation suite that tests its features. **The Selenium/CI system is the assignment's primary deliverable.**

## ⚡ Windows quick start (easiest route)

Prerequisites: **Python 3.11+**, **Java JDK 17+**, **Apache Maven 3.9+** and **Google Chrome**. The first run requires internet access for Python and Maven dependencies. No Docker required.

**1. Start the site:** Unzip everything, then double-click `start_windows.bat`. Leave its command window open. Visit **http://127.0.0.1:8000**.

**2. On the portal chooser, select the account type. Admin and student have different login pages.**

- Administrator portal: `http://127.0.0.1:8000/admin/login`
- Student portal: `http://127.0.0.1:8000/student/login`

**Demo credentials (each works only on its own portal):**

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `Admin@123` |
| Read-only user | `student` | `Student@123` |

**3. Run automated tests:** Double-click `run_tests_windows.bat` from the same project folder **while the first window remains open**. It starts visible Chrome browser automation and produces `target/extent-report/index.html`.

Or, in PowerShell (inside the extracted project folder):

```powershell
# Terminal 1 — website + special test isolation mode
$env:TEST_MODE="1"
$env:TEST_TOKEN="local-ci-demo-token"
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
# Terminal 2 — Selenium/TestNG/Maven test runner
$env:TEST_TOKEN="local-ci-demo-token"
mvn clean test -Dheadless=false -DbaseUrl=http://127.0.0.1:8000
```

> `TEST_MODE=1` enables a token-protected test-only database reset endpoint so Selenium tests get the same 25 sample rows each time. **Never enable test mode on a public deployment.** The tests actively reset sample attendance data: do not run them against real college records.

## Your exact requirements and their implementation

| Faculty requirement | Where it is implemented |
|---|---|
| Student-built management web application | `app/main.py`, `app/templates/`, `app/static/` |
| Admin and normal-user roles | Separate `/admin/login` and `/student/login` pages, signed session cookies, server-enforced `/admin` and CRUD API restrictions |
| Admin sees admin pages, user denied | TC03, TC04, TC05 (also TC14) |
| Add / Edit / Delete / Search records | TC07–TC11 |
| Verify table data and pagination | TC12–TC14 |
| CSV file upload and report download | TC15–TC18 |
| Selenium WebDriver | Java browser automation in `src/test/java/` |
| TestNG | Java `@Test`, suite defined in `testng.xml` |
| Maven | `pom.xml`, `mvn clean test` |
| ExtentReports HTML test report | `ExtentListener.java`, output `target/extent-report/index.html` |
| Automated CI run on every push | `.github/workflows/selenium-ci.yml` (`push`, `pull_request`, manual trigger) |
| Demonstrate a deliberately broken feature | Change `SEARCH_BUG_ENABLED` in `app/config.py`, push, see failed `searchReturnsOnlyMatchingStudent` test |
| Evidence when test fails | ExtentReports HTML, TestNG/Surefire XML, error details + PNG screenshot (`target/screenshots/`) |

## Architecture

```text
                    ATTENDANCE MANAGEMENT WEBSITE
                  Python FastAPI + SQLite + HTML/JS
                               |
         Chrome browser actions via Java Selenium WebDriver
                               |
             TestNG assertions and Maven test runner
                               |
           ExtentReports HTML + failure screenshots
                               ^
            GitHub Actions runs suite on every push
```

The website is deliberately lightweight so you can spend time showing the **automated tests**. The backend uses FastAPI (not Flask; either is valid for the assignment's example application). Selenium testing remains **Java + TestNG + Maven**, as required.

## What the website does

- At `/login`, choose **Administrator portal** or **Student portal**, then use only that portal's credentials. Admin: `/admin/login`; student: `/student/login`. Each form accepts only its own role.
- Admin can create, read, update, delete, and search attendance records. These actions are checked on the server; disabling the UI is not the only security control.
- Viewer can search and browse data and download permitted reports; cannot edit records or access `/admin`.
- Student directory supports 10 rows per page, next/previous navigation, and verified columns.
- Admin can upload a UTF-8 CSV with valid headers and download sample CSV template.
- Both roles can export CSV reports. Exports include the current search filter.
- Demo database has 25 seeded records covering 3 pages.
- Import rejects invalid rows and duplicate IDs transactionally.

## Test case table (21 Selenium tests)

| ID | TestNG method | Feature/expected outcome |
|---|---|---|
| TC01 | `adminLoginSucceeds` | Admin login opens dashboard |
| TC02 | `normalUserLoginSucceeds` | User login gets read-only role |
| TC03 | `adminCanOpenAdminConsole` | Admin console visible and accessible |
| TC04 | `normalUserCannotAccessAdminPage` | Hidden link + direct URL rejected |
| TC05 | `normalUserCannotCreateRecords` | Server responds HTTP 403 |
| TC06 | `invalidLoginIsRejected` | Wrong password rejected |
| TC07 | `createAttendanceRecord` | Add new record and verify row |
| TC08 | `updateAttendanceRecord` | Edit name/status and verify |
| TC09 | `deleteAttendanceRecord` | Delete and verify absence |
| TC10 | `searchReturnsOnlyMatchingStudent` | Exactly one matching student (regression detector) |
| TC11 | `searchNoResults` | Empty-state feedback |
| TC12 | `tableContainsCorrectData` | Seeded row and 10 per page |
| TC13 | `paginationNextAndPrevious` | Pages 1 and 2 show appropriate rows |
| TC14 | `viewerCannotEditTable` | User sees no modify controls |
| TC15 | `validCsvUpload` | Two records imported from CSV |
| TC16 | `invalidCsvUploadRejected` | Invalid CSV rejected, record total unchanged |
| TC17 | `reportDownloadsCorrectCsv` | Actual CSV file downloaded; headings + seeded data verified |
| TC18 | `userCanDownloadReport` | Viewer CSV report download works |

Tests are intentionally isolated and executed **sequentially**. `@BeforeMethod` resets the seeded data and launches a fresh Chrome session; `@AfterMethod` closes the browser. Every success/failure is captured in ExtentReports; failures additionally save PNG evidence when possible.

## GitHub Actions — automatically test every pushed commit

GitHub Actions workflow is already in `.github/workflows/selenium-ci.yml`, so **upload all files including hidden `.github` directory** to a repository.

On each push or pull request, CI performs these steps:

1. Checkout code and set up Python + Java 17.
2. Install web app dependencies.
3. Start the FastAPI attendance server in the background and wait until healthy.
4. Run `mvn clean test` in headless Chrome with Selenium + TestNG.
5. Run additional Python API tests even if Selenium detects a failure.
6. Always upload ExtentReports, Surefire results, screenshots and app logs as downloadable CI artifacts.

How to view: **Repository → Actions → CampusTrack - Selenium Regression CI → a workflow run → Artifacts → download `campustrack-test-evidence-...` → extract → `target/extent-report/index.html`**. The test suite's workflow step will be marked red when any tests fail.

### Faculty demo — intentionally break search, then prove CI catches it

1. First push the working code to GitHub. Wait for **green CI** and download its pass report.
2. In `app/config.py`, change `SEARCH_BUG_ENABLED = False` to `SEARCH_BUG_ENABLED = True`.
3. Run `git add app/config.py`, `git commit -m "Demo: introduce search regression"`, `git push`.
4. Open **GitHub → Actions**. The pushed commit starts a new CI run automatically.
5. Show the **red CI run**, failed `searchReturnsOnlyMatchingStudent` and failed search assertions in ExtentReports. The API search test will also fail.
6. Change `True` back to `False`, commit `git commit -am "Fix: restore attendance search"`, and `git push` again.
7. Show the next **green CI run** and successful report.

**Important:** Don't change the Selenium tests to make them fail. Change the *application code*, allowing the original tests to detect an actual regression. Use a separate demo branch if the original repository must stay stable. CI triggers on pushes to all branches.

### First push from PowerShell (create an EMPTY repository on GitHub first)

```powershell
git init
git add .
git commit -m "Initial CampusTrack attendance application and Selenium CI suite"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Replace `YOUR-USERNAME` and `YOUR-REPOSITORY` with your actual repository details. GitHub authentication will be required. If you already initialized the repository, do not repeat `git init` and `git remote add`.

## Optional Docker Desktop route (website only)

```powershell
docker compose up --build -d
```

Visit http://localhost:8000. This runs the attendance website but **does not automatically run Selenium tests**. The Compose file disables the test-reset endpoint by default to avoid wiping student data. For the full local test demonstration, prefer `start_windows.bat` + `run_tests_windows.bat`, or configure a test-only environment explicitly.

To stop website: `docker compose down` (Docker route), or `Ctrl+C` in the server terminal (Windows direct route).

## Troubleshooting

- **`mvn` not recognized:** Install Apache Maven, ensure `JAVA_HOME` points to JDK 17+, add Maven `bin` to PATH, then reopen PowerShell. `mvn -version` should work.
- **`py` not recognized:** Install Python 3.11+ from python.org and add it to PATH.
- **Chrome / driver error:** Install/update Chrome. Selenium Manager handles matching ChromeDriver automatically (internet might be needed initially).
- **Test reset 404 or 403:** Tests require server started using `TEST_MODE=1` and matching `TEST_TOKEN=local-ci-demo-token`.
- **Tests all fail to start:** Leave website terminal open, ensure http://127.0.0.1:8000/login and both role-specific login pages work, and verify no other server is using port 8000.
- **Download test failure:** Verify Chrome download permissions and that the selected download directory is writable.
- **Report missing:** Verify Maven reached the TestNG suite and did not fail earlier during dependency downloads.
- **Actions workflow fails to start:** Check that `.github/workflows/selenium-ci.yml` was committed, and repository Actions are enabled.
- **Demo feature break does not appear:** Confirm the `True` change was committed and pushed; in the Action run details verify commit SHA.

## Security / production limitations

Designed as a classroom project, not as a production university service. Demo credentials are public; change secrets and enable TLS / CSRF protection / better permission modelling before public deployment. Cookies are configured for localhost HTTP demonstration. Tests reset synthetic attendance records only; never run `TEST_MODE=1` on a real data system. SQLite is sufficient for demonstration but not high-concurrency production workloads. The workflow's test results and screenshots are genuine **only after GitHub Actions executes**, not pre-generated.

## Docs

- `docs/DEMO_SCRIPT.md`: viva/presentation walkthrough with speaking notes.
- `docs/PROJECT_REPORT.md`: introduction, objectives, architecture, modules, outcomes, limitations and future scope.
- `docs/TEST_CASE_MATRIX.csv`: detailed cases with steps and expected results.
- `docs/VERIFICATION.md`: which checks were performed in packaging, what still requires live CI verification.

## Group No. 10: Separate authentication portals

- Visit `http://127.0.0.1:8000/login` to choose a portal; **there is no combined sign-in form**.
- Admin goes to `/admin/login` with `admin` / `Admin@123`, lands in the admin attendance dashboard (`/`) and can open `/admin`.
- Student goes to `/student/login` with `student` / `Student@123`, lands in the **read-only student attendance portal** (`/student`).
- Students do not see admin navigation, add/edit/delete buttons, or CSV upload. Direct requests to `/admin` and mutating APIs are refused with HTTP 403.
- Logging in through the wrong portal is refused even if the username and password are correct.
- Selenium now includes three additional role-portal tests (TC19–TC21) for a total of 21 cases.

**Demonstration:** log in as admin, open `/admin`, log out, then log in as student. Show the separate page and try the admin URL — it is blocked. Run `run_tests_windows.bat` to show the regression suite.
