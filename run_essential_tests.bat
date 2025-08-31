@echo off
REM E-Commerce Platform - Essential Test Runner (Windows)
REM This script runs only the essential tests needed to verify platform functionality

setlocal enabledelayedexpansion

REM Colors (limited in Windows CMD)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Test configuration
set QUICK_MODE=false
set FULL_MODE=false
set COMPLETE_MODE=false
set VERBOSE=false

REM Parse command line arguments
:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="--quick" (
    set QUICK_MODE=true
    shift
    goto parse_args
)
if "%~1"=="--full" (
    set FULL_MODE=true
    shift
    goto parse_args
)
if "%~1"=="--complete" (
    set COMPLETE_MODE=true
    shift
    goto parse_args
)
if "%~1"=="--verbose" (
    set VERBOSE=true
    shift
    goto parse_args
)
if "%~1"=="-v" (
    set VERBOSE=true
    shift
    goto parse_args
)
if "%~1"=="--help" goto show_help
if "%~1"=="-h" goto show_help

echo Unknown option: %~1
echo Use --help for usage information
exit /b 1

:show_help
echo Usage: %0 [OPTIONS]
echo.
echo Options:
echo   --quick      Run only critical tests (2 minutes)
echo   --full       Run critical + important tests (5 minutes)
echo   --complete   Run all tests including optional (15 minutes)
echo   --verbose    Enable verbose output
echo   --help       Show this help message
echo.
echo Default: Run critical tests
exit /b 0

:end_parse

REM Set default mode if none specified
if "%QUICK_MODE%"=="false" if "%FULL_MODE%"=="false" if "%COMPLETE_MODE%"=="false" (
    set FULL_MODE=true
)

REM Function to print colored output (limited in Windows)
:print_status
echo %~2
goto :eof

REM Function to print section headers
:print_section
echo.
echo ==================================================
echo %~1
echo ==================================================
goto :eof

REM Check prerequisites
:check_prerequisites
call :print_section "Checking Prerequisites"

REM Check if we're in the right directory
if not exist "backend" if not exist "manage.py" (
    echo Error: Please run this script from the project root directory
    exit /b 1
)

REM Navigate to project root if we're in backend
if exist "manage.py" cd ..

REM Check required directories
if not exist "backend" (
    echo Error: Directory backend not found
    exit /b 1
)
if not exist "frontend" (
    echo Error: Directory frontend not found
    exit /b 1
)
if not exist "qa-testing-framework" (
    echo Error: Directory qa-testing-framework not found
    exit /b 1
)

echo Prerequisites check completed
goto :eof

REM Run backend tests
:run_backend_tests
set test_level=%~1
call :print_section "Backend Tests (%test_level%)"

cd backend

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" call venv\Scripts\activate.bat

set failed_tests=0

REM Critical backend tests
if "%test_level%"=="quick" goto run_critical_backend
if "%test_level%"=="full" goto run_critical_backend
if "%test_level%"=="complete" goto run_critical_backend
goto skip_critical_backend

:run_critical_backend
echo Running: Database Models Test
python manage.py test tests.unit.test_models --verbosity=2
if errorlevel 1 set /a failed_tests+=1

echo Running: API Views Test
python manage.py test tests.unit.test_views --verbosity=2
if errorlevel 1 set /a failed_tests+=1

echo Running: System Integration Test
python manage.py test tests.integration.test_system_integration --verbosity=2
if errorlevel 1 set /a failed_tests+=1

:skip_critical_backend

REM Important backend tests
if "%test_level%"=="full" goto run_important_backend
if "%test_level%"=="complete" goto run_important_backend
goto skip_important_backend

:run_important_backend
echo Running: API Integration Test
python manage.py test tests.integration.test_api_integration --verbosity=2
if errorlevel 1 set /a failed_tests+=1

echo Running: User Journey Test
python manage.py test tests.integration.test_user_journey --verbosity=2
if errorlevel 1 set /a failed_tests+=1

echo Running: Payment Integration Test
python manage.py test tests.integration.test_payment_integrations --verbosity=2
if errorlevel 1 set /a failed_tests+=1

echo Running: Security Test
python manage.py test tests.security.test_security --verbosity=2
if errorlevel 1 set /a failed_tests+=1

:skip_important_backend

REM Optional backend tests
if "%test_level%"=="complete" goto run_optional_backend
goto skip_optional_backend

:run_optional_backend
echo Running: Performance Test
python manage.py test tests.performance.test_load_testing --verbosity=2
if errorlevel 1 set /a failed_tests+=1

echo Running: Migration Test
python manage.py test tests.test_migration_comprehensive --verbosity=2
if errorlevel 1 set /a failed_tests+=1

:skip_optional_backend

cd ..
exit /b %failed_tests%

REM Run frontend tests
:run_frontend_tests
set test_level=%~1
call :print_section "Frontend Tests (%test_level%)"

cd frontend

set failed_tests=0

REM Critical frontend tests
if "%test_level%"=="quick" goto run_critical_frontend
if "%test_level%"=="full" goto run_critical_frontend
if "%test_level%"=="complete" goto run_critical_frontend
goto skip_critical_frontend

:run_critical_frontend
echo Running: Dashboard Component Test
npm test -- --testPathPattern="Dashboard.test.tsx" --watchAll=false
if errorlevel 1 set /a failed_tests+=1

echo Running: Admin Login Test
npm test -- --testPathPattern="AdminLogin.test.tsx" --watchAll=false
if errorlevel 1 set /a failed_tests+=1

:skip_critical_frontend

REM Important frontend tests
if "%test_level%"=="full" goto run_important_frontend
if "%test_level%"=="complete" goto run_important_frontend
goto skip_important_frontend

:run_important_frontend
echo Running: API Client Test
npm test -- --testPathPattern="services/apiClient.test.ts" --watchAll=false
if errorlevel 1 set /a failed_tests+=1

echo Running: Frontend Build Test
npm run build
if errorlevel 1 set /a failed_tests+=1

:skip_important_frontend

cd ..
exit /b %failed_tests%

REM Run QA framework tests
:run_qa_tests
set test_level=%~1
call :print_section "QA Framework Tests (%test_level%)"

cd qa-testing-framework

set failed_tests=0

REM Critical QA tests
if "%test_level%"=="quick" goto run_critical_qa
if "%test_level%"=="full" goto run_critical_qa
if "%test_level%"=="complete" goto run_critical_qa
goto skip_critical_qa

:run_critical_qa
echo Running: Authentication E2E Test
python -m pytest web/test_authentication.py -v
if errorlevel 1 set /a failed_tests+=1

echo Running: Shopping Cart E2E Test
python -m pytest web/test_shopping_cart_checkout.py -v
if errorlevel 1 set /a failed_tests+=1

:skip_critical_qa

REM Important QA tests
if "%test_level%"=="full" goto run_important_qa
if "%test_level%"=="complete" goto run_important_qa
goto skip_important_qa

:run_important_qa
echo Running: Payment Processing E2E Test
python -m pytest web/test_payment_processing.py -v
if errorlevel 1 set /a failed_tests+=1

echo Running: API Authentication Test
python -m pytest api/test_authentication.py -v
if errorlevel 1 set /a failed_tests+=1

:skip_important_qa

cd ..
exit /b %failed_tests%

REM Main execution
:main
set start_time=%time%

call :print_section "E-Commerce Platform - Essential Test Runner"

REM Determine test level
if "%QUICK_MODE%"=="true" (
    set test_level=quick
    echo Mode: Quick (Critical tests only - ~2 minutes)
) else if "%FULL_MODE%"=="true" (
    set test_level=full
    echo Mode: Full (Critical + Important tests - ~5 minutes)
) else if "%COMPLETE_MODE%"=="true" (
    set test_level=complete
    echo Mode: Complete (All tests - ~15 minutes)
)

REM Check prerequisites
call :check_prerequisites
if errorlevel 1 exit /b 1

REM Run health checks
call :print_section "System Health Checks"
echo Running: Database Connectivity
cd backend
python manage.py check --database default
set health_failures=%errorlevel%
cd ..

REM Run tests
set total_failures=0

call :run_backend_tests %test_level%
set /a total_failures+=%errorlevel%

call :run_frontend_tests %test_level%
set /a total_failures+=%errorlevel%

call :run_qa_tests %test_level%
set /a total_failures+=%errorlevel%

REM Print summary
call :print_section "Test Summary"
echo Health Check Failures: %health_failures%
echo Test Failures: %total_failures%

if %total_failures% equ 0 (
    echo.
    echo ALL ESSENTIAL TESTS PASSED!
    echo Platform is ready for deployment
    exit /b 0
) else (
    echo.
    echo %total_failures% TESTS FAILED
    echo Platform has issues - review failed tests before deployment
    exit /b 1
)

REM Run main function
call :main %*