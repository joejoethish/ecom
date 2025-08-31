#!/bin/bash

# E-Commerce Platform - Essential Test Runner
# This script runs only the essential tests needed to verify platform functionality

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
QUICK_MODE=false
FULL_MODE=false
COMPLETE_MODE=false
PARALLEL_MODE=true
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --full)
            FULL_MODE=true
            shift
            ;;
        --complete)
            COMPLETE_MODE=true
            shift
            ;;
        --no-parallel)
            PARALLEL_MODE=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick      Run only critical tests (2 minutes)"
            echo "  --full       Run critical + important tests (5 minutes)"
            echo "  --complete   Run all tests including optional (15 minutes)"
            echo "  --no-parallel Disable parallel test execution"
            echo "  --verbose    Enable verbose output"
            echo "  --help       Show this help message"
            echo ""
            echo "Default: Run critical tests in parallel mode"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set default mode if none specified
if [[ "$QUICK_MODE" == false && "$FULL_MODE" == false && "$COMPLETE_MODE" == false ]]; then
    FULL_MODE=true
fi

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print section headers
print_section() {
    echo ""
    print_status $BLUE "=================================================="
    print_status $BLUE "$1"
    print_status $BLUE "=================================================="
}

# Function to run command with error handling
run_command() {
    local description=$1
    local command=$2
    local directory=$3
    
    print_status $YELLOW "Running: $description"
    
    if [[ -n "$directory" ]]; then
        cd "$directory"
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        echo "Command: $command"
        echo "Directory: $(pwd)"
    fi
    
    if eval "$command"; then
        print_status $GREEN "✅ $description - PASSED"
        return 0
    else
        print_status $RED "❌ $description - FAILED"
        return 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_section "Checking Prerequisites"
    
    # Check if we're in the right directory
    if [[ ! -f "manage.py" ]] && [[ ! -d "backend" ]]; then
        print_status $RED "❌ Please run this script from the project root directory"
        exit 1
    fi
    
    # Navigate to project root if we're in backend
    if [[ -f "manage.py" ]]; then
        cd ..
    fi
    
    # Check required directories
    for dir in "backend" "frontend" "qa-testing-framework"; do
        if [[ ! -d "$dir" ]]; then
            print_status $RED "❌ Directory $dir not found"
            exit 1
        fi
    done
    
    # Check Python virtual environment
    if [[ ! -d "backend/venv" ]] && [[ -z "$VIRTUAL_ENV" ]]; then
        print_status $YELLOW "⚠️  No Python virtual environment detected"
        print_status $YELLOW "   Consider creating one: cd backend && python -m venv venv"
    fi
    
    # Check Node.js dependencies
    if [[ ! -d "frontend/node_modules" ]]; then
        print_status $YELLOW "⚠️  Frontend dependencies not installed"
        print_status $YELLOW "   Run: cd frontend && npm install"
    fi
    
    print_status $GREEN "✅ Prerequisites check completed"
}

# Function to run backend tests
run_backend_tests() {
    local test_level=$1
    print_section "Backend Tests ($test_level)"
    
    cd backend
    
    # Activate virtual environment if it exists
    if [[ -d "venv" ]]; then
        source venv/bin/activate
    fi
    
    local failed_tests=0
    
    # Critical backend tests
    if [[ "$test_level" == "quick" ]] || [[ "$test_level" == "full" ]] || [[ "$test_level" == "complete" ]]; then
        run_command "Database Models Test" "python manage.py test tests.unit.test_models --verbosity=2" || ((failed_tests++))
        run_command "API Views Test" "python manage.py test tests.unit.test_views --verbosity=2" || ((failed_tests++))
        run_command "System Integration Test" "python manage.py test tests.integration.test_system_integration --verbosity=2" || ((failed_tests++))
    fi
    
    # Important backend tests
    if [[ "$test_level" == "full" ]] || [[ "$test_level" == "complete" ]]; then
        run_command "API Integration Test" "python manage.py test tests.integration.test_api_integration --verbosity=2" || ((failed_tests++))
        run_command "User Journey Test" "python manage.py test tests.integration.test_user_journey --verbosity=2" || ((failed_tests++))
        run_command "Payment Integration Test" "python manage.py test tests.integration.test_payment_integrations --verbosity=2" || ((failed_tests++))
        run_command "Security Test" "python manage.py test tests.security.test_security --verbosity=2" || ((failed_tests++))
    fi
    
    # Optional backend tests
    if [[ "$test_level" == "complete" ]]; then
        run_command "Performance Test" "python manage.py test tests.performance.test_load_testing --verbosity=2" || ((failed_tests++))
        run_command "Migration Test" "python manage.py test tests.test_migration_comprehensive --verbosity=2" || ((failed_tests++))
        run_command "Debugging System Test" "python manage.py test tests.e2e.test_workflow_debugging_e2e --verbosity=2" || ((failed_tests++))
    fi
    
    cd ..
    return $failed_tests
}

# Function to run frontend tests
run_frontend_tests() {
    local test_level=$1
    print_section "Frontend Tests ($test_level)"
    
    cd frontend
    
    local failed_tests=0
    
    # Critical frontend tests
    if [[ "$test_level" == "quick" ]] || [[ "$test_level" == "full" ]] || [[ "$test_level" == "complete" ]]; then
        run_command "Dashboard Component Test" "npm test -- --testPathPattern='Dashboard.test.tsx' --watchAll=false" || ((failed_tests++))
        run_command "Admin Login Test" "npm test -- --testPathPattern='AdminLogin.test.tsx' --watchAll=false" || ((failed_tests++))
    fi
    
    # Important frontend tests
    if [[ "$test_level" == "full" ]] || [[ "$test_level" == "complete" ]]; then
        run_command "API Client Test" "npm test -- --testPathPattern='services/apiClient.test.ts' --watchAll=false" || ((failed_tests++))
        run_command "Authentication Integration Test" "npm test -- --testPathPattern='integration/authenticationIntegration.test.tsx' --watchAll=false" || ((failed_tests++))
    fi
    
    # Optional frontend tests
    if [[ "$test_level" == "complete" ]]; then
        run_command "Correlation ID Test" "npm test -- --testPathPattern='hooks/useCorrelationId.test.ts' --watchAll=false" || ((failed_tests++))
        run_command "E2E Workflow Debugging Test" "npm test -- --testPathPattern='e2e/workflow-debugging.test.tsx' --watchAll=false" || ((failed_tests++))
    fi
    
    # Build test (always run for full and complete)
    if [[ "$test_level" == "full" ]] || [[ "$test_level" == "complete" ]]; then
        run_command "Frontend Build Test" "npm run build" || ((failed_tests++))
    fi
    
    cd ..
    return $failed_tests
}

# Function to run QA framework tests
run_qa_tests() {
    local test_level=$1
    print_section "QA Framework Tests ($test_level)"
    
    cd qa-testing-framework
    
    local failed_tests=0
    
    # Critical QA tests
    if [[ "$test_level" == "quick" ]] || [[ "$test_level" == "full" ]] || [[ "$test_level" == "complete" ]]; then
        run_command "Authentication E2E Test" "python -m pytest web/test_authentication.py -v" || ((failed_tests++))
        run_command "Shopping Cart E2E Test" "python -m pytest web/test_shopping_cart_checkout.py -v" || ((failed_tests++))
    fi
    
    # Important QA tests
    if [[ "$test_level" == "full" ]] || [[ "$test_level" == "complete" ]]; then
        run_command "Payment Processing E2E Test" "python -m pytest web/test_payment_processing.py -v" || ((failed_tests++))
        run_command "Product Browsing E2E Test" "python -m pytest web/test_product_browsing.py -v" || ((failed_tests++))
        run_command "API Authentication Test" "python -m pytest api/test_authentication.py -v" || ((failed_tests++))
        run_command "API Product Order Test" "python -m pytest api/test_product_order_management.py -v" || ((failed_tests++))
    fi
    
    # Optional QA tests
    if [[ "$test_level" == "complete" ]]; then
        run_command "Mobile Authentication Test" "python -m pytest mobile/test_mobile_auth.py -v" || ((failed_tests++))
        run_command "Mobile Shopping Test" "python -m pytest mobile/test_mobile_shopping.py -v" || ((failed_tests++))
        run_command "API Performance Test" "python -m pytest api/test_performance.py -v" || ((failed_tests++))
    fi
    
    cd ..
    return $failed_tests
}

# Function to run health checks
run_health_checks() {
    print_section "System Health Checks"
    
    local failed_checks=0
    
    # Database connectivity check
    run_command "Database Connectivity" "cd backend && python manage.py check --database default" || ((failed_checks++))
    
    # Basic API connectivity check
    run_command "API Connectivity" "cd qa-testing-framework && python -m pytest api/test_api_client.py::TestAPIClient::test_api_connectivity -v" || ((failed_checks++))
    
    return $failed_checks
}

# Function to run tests in parallel
run_tests_parallel() {
    local test_level=$1
    print_section "Running Tests in Parallel Mode ($test_level)"
    
    # Create temporary files for results
    local backend_result=$(mktemp)
    local frontend_result=$(mktemp)
    local qa_result=$(mktemp)
    
    # Run tests in background
    (run_backend_tests "$test_level"; echo $? > "$backend_result") &
    local backend_pid=$!
    
    (run_frontend_tests "$test_level"; echo $? > "$frontend_result") &
    local frontend_pid=$!
    
    (run_qa_tests "$test_level"; echo $? > "$qa_result") &
    local qa_pid=$!
    
    # Wait for all tests to complete
    print_status $YELLOW "Waiting for parallel tests to complete..."
    wait $backend_pid $frontend_pid $qa_pid
    
    # Read results
    local backend_failures=$(cat "$backend_result")
    local frontend_failures=$(cat "$frontend_result")
    local qa_failures=$(cat "$qa_result")
    
    # Cleanup
    rm -f "$backend_result" "$frontend_result" "$qa_result"
    
    return $((backend_failures + frontend_failures + qa_failures))
}

# Function to run tests sequentially
run_tests_sequential() {
    local test_level=$1
    print_section "Running Tests in Sequential Mode ($test_level)"
    
    local total_failures=0
    
    run_backend_tests "$test_level"
    total_failures=$((total_failures + $?))
    
    run_frontend_tests "$test_level"
    total_failures=$((total_failures + $?))
    
    run_qa_tests "$test_level"
    total_failures=$((total_failures + $?))
    
    return $total_failures
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    print_section "E-Commerce Platform - Essential Test Runner"
    
    # Determine test level
    local test_level=""
    if [[ "$QUICK_MODE" == true ]]; then
        test_level="quick"
        print_status $BLUE "Mode: Quick (Critical tests only - ~2 minutes)"
    elif [[ "$FULL_MODE" == true ]]; then
        test_level="full"
        print_status $BLUE "Mode: Full (Critical + Important tests - ~5 minutes)"
    elif [[ "$COMPLETE_MODE" == true ]]; then
        test_level="complete"
        print_status $BLUE "Mode: Complete (All tests - ~15 minutes)"
    fi
    
    # Check prerequisites
    check_prerequisites
    
    # Run health checks first
    run_health_checks
    local health_failures=$?
    
    if [[ $health_failures -gt 0 ]]; then
        print_status $RED "⚠️  Health checks failed. Continuing with tests but issues may occur."
    fi
    
    # Run tests
    local test_failures=0
    if [[ "$PARALLEL_MODE" == true ]]; then
        run_tests_parallel "$test_level"
        test_failures=$?
    else
        run_tests_sequential "$test_level"
        test_failures=$?
    fi
    
    # Calculate execution time
    local end_time=$(date +%s)
    local execution_time=$((end_time - start_time))
    local minutes=$((execution_time / 60))
    local seconds=$((execution_time % 60))
    
    # Print summary
    print_section "Test Summary"
    print_status $BLUE "Execution Time: ${minutes}m ${seconds}s"
    print_status $BLUE "Health Check Failures: $health_failures"
    print_status $BLUE "Test Failures: $test_failures"
    
    if [[ $test_failures -eq 0 ]]; then
        print_status $GREEN "🎉 ALL ESSENTIAL TESTS PASSED!"
        print_status $GREEN "✅ Platform is ready for deployment"
        exit 0
    else
        print_status $RED "❌ $test_failures TESTS FAILED"
        print_status $RED "🚨 Platform has issues - review failed tests before deployment"
        exit 1
    fi
}

# Run main function
main "$@"