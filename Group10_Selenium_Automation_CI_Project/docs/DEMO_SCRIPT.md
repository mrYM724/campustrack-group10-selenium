# Presentation Demo Script — Selenium Automation / Group No. 10

## First prepare

1. Run `start_windows.bat`, leave the terminal open.
2. Open http://127.0.0.1:8000/login → **Administrator portal** (`/admin/login`), then log in as `admin` / `Admin@123`.
3. Prepare a second window with `run_tests_windows.bat` (do not click until the application is ready).
4. Open your GitHub repository and its **Actions** tab for automated CI proof.

## First teammate — attendance website (~1 minute)

"This is our Attendance Management System, called CampusTrack. The administrator can add, update, delete and search attendance records. The normal user can view data but cannot access admin pages. The table supports pagination; administrators can import attendance CSV files, and users can download reports. We use a Python backend and SQLite database."

Show login as administrator, create a record, search for it, edit it, and delete it. Then show the import/download controls. Log out, choose **Student portal** (`/student/login`) and sign in as `student` / `Student@123`. Show that this is a separate read-only page, that edit buttons and the admin link are absent, and that manually opening `/admin` returns HTTP 403.

## Second teammate — Selenium tests (~1 minute)

"Manual regression testing is repetitive. We use Selenium WebDriver to automatically control Chrome and test website functions. TestNG groups test cases and checks expected outcomes, while Maven installs the required libraries and runs the test suite."

Run `run_tests_windows.bat` or `mvn clean test -Dheadless=false`. Selenium should open Chrome and exercise all the test cases automatically. The suite includes role access, CRUD, search, pagination, CSV upload and report download.

## Third teammate — ExtentReports + CI (~1 minute)

"ExtentReports generates a structured HTML report showing test pass/fail statuses. For failed tests, our framework captures a screenshot to help debug the issue. GitHub Actions starts the suite automatically whenever we push code changes."

Show `target/extent-report/index.html`, then GitHub Actions tab and a successful run. Explain that test jobs run headlessly in GitHub's remote Linux environment.

## Final demo — break/fix (~1–2 minutes plus CI execution)

Before the live demo, make a successful baseline commit and a second intentionally broken commit if internet or execution time is limited. **Do not pretend this is live if showing pre-recorded evidence; explain that they are earlier actual GitHub runs.**

1. Open `app/config.py` and change `SEARCH_BUG_ENABLED` from `False` to `True`.
2. Commit and push only the application change.
3. Show GitHub Actions triggering automatically and marking the Selenium run red.
4. Open the failing Extent report, locate `searchReturnsOnlyMatchingStudent` and its screenshot.
5. Revert change, push again, and show it turns green.

Explain: "We intentionally broke the application search, not the tests. The unchanged tests detected the bug automatically, proving regression testing works after code changes."

## Viva short answers

- **Selenium?** A browser automation tool.
- **WebDriver?** Browser control API used by Selenium.
- **TestNG?** Java framework for organising test cases and verifying outcomes.
- **Maven?** Java build and dependency manager.
- **ExtentReports?** HTML report of execution results, screenshots and errors.
- **CI?** Automatically build and test code after developers push changes.
- **Regression testing?** Re-checking existing features after a code change.
- **CRUD?** Create, Read, Update, Delete.
- **Pagination?** Dividing a long table into pages.
- **Role-based access?** Administrator has more permissions than normal users.
- **Why failure screenshot?** It provides evidence of what the browser looked like when the assertion failed.
- **Why GitHub Actions?** Automatic test execution without running tests manually after every commit.
