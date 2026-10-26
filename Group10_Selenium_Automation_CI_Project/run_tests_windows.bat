@echo off
setlocal
cd /d "%~dp0"
echo CAMP USTRACK SELENIUM REGRESSION SUITE
where mvn >nul 2>&1
if errorlevel 1 (
  echo Maven was not found. Install Maven 3.9+ and add its bin folder to PATH.
  pause
  exit /b 1
)
set "TEST_TOKEN=local-ci-demo-token"
echo Running browser tests with visible Chrome...
mvn clean test -Dheadless=false -DbaseUrl=http://127.0.0.1:8000
set "RESULT=%errorlevel%"
echo.
echo HTML report: target\extent-report\index.html
echo TestNG / Maven results: target\surefire-reports\
if not "%RESULT%"=="0" echo At least one test FAILED. Open the Extent report.
pause
exit /b %RESULT%
