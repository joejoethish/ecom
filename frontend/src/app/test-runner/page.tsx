'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Play, 
  Square, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  FileText,
  Terminal,
  Database,
  Smartphone,
  Globe,
  Server,
  Code,
  Shield,
  Zap
} from 'lucide-react';

interface TestResult {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'passed' | 'failed' | 'skipped';
  duration?: number;
  error?: string;
  file: string;
  category: 'frontend' | 'backend' | 'qa-web' | 'qa-api' | 'qa-mobile' | 'qa-database';
}

interface TestSuite {
  name: string;
  tests: TestResult[];
  status: 'pending' | 'running' | 'completed';
  duration?: number;
  category: 'frontend' | 'backend' | 'qa-web' | 'qa-api' | 'qa-mobile' | 'qa-database';
  icon: React.ReactNode;
}

export default function TestRunnerPage() {
  const [isRunning, setIsRunning] = useState(false);
  const [testSuites, setTestSuites] = useState<TestSuite[]>([]);
  const [selectedSuite, setSelectedSuite] = useState<string>('all');
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);

  // Comprehensive test data based on actual project structure
  const mockTestSuites: TestSuite[] = [
    {
      name: 'Frontend Component Tests',
      status: 'pending',
      category: 'frontend',
      icon: <Code className="h-4 w-4" />,
      tests: [
        // Authentication Components
        { id: '1', name: 'AuthGuard component tests', status: 'pending', file: 'components/auth/__tests__/AuthGuard.test.tsx', category: 'frontend' },
        { id: '2', name: 'EmailVerificationPage tests', status: 'pending', file: 'components/auth/__tests__/EmailVerificationPage.test.tsx', category: 'frontend' },
        { id: '3', name: 'LoginForm component tests', status: 'pending', file: 'components/auth/__tests__/LoginForm.test.tsx', category: 'frontend' },
        { id: '4', name: 'ForgotPasswordForm tests', status: 'pending', file: 'components/auth/__tests__/ForgotPasswordForm.test.tsx', category: 'frontend' },
        { id: '5', name: 'ResetPasswordForm tests', status: 'pending', file: 'components/auth/__tests__/ResetPasswordForm.test.tsx', category: 'frontend' },
        
        // Product Components
        { id: '6', name: 'ProductGrid component tests', status: 'pending', file: 'components/products/__tests__/ProductGrid.test.tsx', category: 'frontend' },
        { id: '7', name: 'ProductCard component tests', status: 'pending', file: 'components/products/__tests__/ProductCard.test.tsx', category: 'frontend' },
        { id: '8', name: 'ProductDetails component tests', status: 'pending', file: 'components/products/__tests__/ProductDetails.test.tsx', category: 'frontend' },
        { id: '9', name: 'ProductFilters component tests', status: 'pending', file: 'components/products/__tests__/ProductFilters.test.tsx', category: 'frontend' },
        { id: '10', name: 'CategoryNavigation tests', status: 'pending', file: 'components/products/__tests__/CategoryNavigation.test.tsx', category: 'frontend' },
        { id: '11', name: 'Pagination component tests', status: 'pending', file: 'components/products/__tests__/Pagination.test.tsx', category: 'frontend' },
        
        // Cart Components
        { id: '12', name: 'CartItem component tests', status: 'pending', file: 'components/cart/__tests__/CartItem.test.tsx', category: 'frontend' },
        { id: '13', name: 'CartSummary component tests', status: 'pending', file: 'components/cart/__tests__/CartSummary.test.tsx', category: 'frontend' },
        { id: '14', name: 'CouponSection tests', status: 'pending', file: 'components/cart/__tests__/CouponSection.test.tsx', category: 'frontend' },
        { id: '15', name: 'SavedItems component tests', status: 'pending', file: 'components/cart/__tests__/SavedItems.test.tsx', category: 'frontend' },
        
        // Search Components
        { id: '16', name: 'SearchAutocomplete tests', status: 'pending', file: 'components/search/__tests__/SearchAutocomplete.test.tsx', category: 'frontend' },
        { id: '17', name: 'SearchBar component tests', status: 'pending', file: 'components/search/__tests__/SearchBar.test.tsx', category: 'frontend' },
        { id: '18', name: 'SearchResults tests', status: 'pending', file: 'components/search/__tests__/SearchResults.test.tsx', category: 'frontend' },
        
        // Order Components
        { id: '19', name: 'OrderHistory component tests', status: 'pending', file: 'components/orders/__tests__/OrderHistory.test.tsx', category: 'frontend' },
        { id: '20', name: 'OrderTracking tests', status: 'pending', file: 'components/orders/__tests__/OrderTracking.test.tsx', category: 'frontend' },
        { id: '21', name: 'ReturnRequestForm tests', status: 'pending', file: 'components/orders/__tests__/ReturnRequestForm.test.tsx', category: 'frontend' },
        
        // Review Components
        { id: '22', name: 'ReviewCard component tests', status: 'pending', file: 'components/reviews/__tests__/ReviewCard.test.tsx', category: 'frontend' },
        { id: '23', name: 'ReviewForm component tests', status: 'pending', file: 'components/reviews/__tests__/ReviewForm.test.tsx', category: 'frontend' },
        { id: '24', name: 'ReviewList component tests', status: 'pending', file: 'components/reviews/__tests__/ReviewList.test.tsx', category: 'frontend' },
        { id: '25', name: 'ReviewSummary tests', status: 'pending', file: 'components/reviews/__tests__/ReviewSummary.test.tsx', category: 'frontend' },
        { id: '26', name: 'StarRating component tests', status: 'pending', file: 'components/reviews/__tests__/StarRating.test.tsx', category: 'frontend' },
        
        // Shipping Components
        { id: '27', name: 'DeliverySlotSelector tests', status: 'pending', file: 'components/shipping/__tests__/DeliverySlotSelector.test.tsx', category: 'frontend' },
        { id: '28', name: 'OrderTrackingInterface tests', status: 'pending', file: 'components/shipping/__tests__/OrderTrackingInterface.test.tsx', category: 'frontend' },
        { id: '29', name: 'ShippingCostCalculator tests', status: 'pending', file: 'components/shipping/__tests__/ShippingCostCalculator.test.tsx', category: 'frontend' },
        { id: '30', name: 'TrackingTimeline tests', status: 'pending', file: 'components/shipping/__tests__/TrackingTimeline.test.tsx', category: 'frontend' },
      ]
    },
    {
      name: 'Frontend Integration Tests',
      status: 'pending',
      category: 'frontend',
      icon: <Globe className="h-4 w-4" />,
      tests: [
        { id: '31', name: 'Dashboard component tests', status: 'pending', file: '__tests__/components/Dashboard.test.tsx', category: 'frontend' },
        { id: '32', name: 'AdminLogin component tests', status: 'pending', file: '__tests__/components/AdminLogin.test.tsx', category: 'frontend' },
        { id: '33', name: 'API Client service tests', status: 'pending', file: '__tests__/services/apiClient.test.ts', category: 'frontend' },
        { id: '34', name: 'Authentication integration tests', status: 'pending', file: '__tests__/integration/authenticationIntegration.test.tsx', category: 'frontend' },
        { id: '35', name: 'Correlation ID integration tests', status: 'pending', file: '__tests__/integration/correlationId.integration.test.ts', category: 'frontend' },
        { id: '36', name: 'Password reset integration tests', status: 'pending', file: '__tests__/integration/passwordReset.integration.test.tsx', category: 'frontend' },
        { id: '37', name: 'useCorrelationId hook tests', status: 'pending', file: '__tests__/hooks/useCorrelationId.test.ts', category: 'frontend' },
        { id: '38', name: 'Workflow debugging E2E tests', status: 'pending', file: '__tests__/e2e/workflow-debugging.test.tsx', category: 'frontend' },
      ]
    },
    {
      name: 'Backend Unit Tests',
      status: 'pending',
      category: 'backend',
      icon: <Server className="h-4 w-4" />,
      tests: [
        { id: '39', name: 'Database models tests', status: 'pending', file: 'tests/unit/test_models.py', category: 'backend' },
        { id: '40', name: 'API views tests', status: 'pending', file: 'tests/unit/test_views.py', category: 'backend' },
        { id: '41', name: 'Migration comprehensive tests', status: 'pending', file: 'tests/test_migration_comprehensive.py', category: 'backend' },
        { id: '42', name: 'Migration edge cases tests', status: 'pending', file: 'tests/test_migration_edge_cases.py', category: 'backend' },
        { id: '43', name: 'API versioning tests', status: 'pending', file: 'tests/test_versioning.py', category: 'backend' },
        { id: '44', name: 'Correlation ID middleware tests', status: 'pending', file: 'tests/test_correlation_id_middleware.py', category: 'backend' },
        { id: '45', name: 'Zero downtime migration tests', status: 'pending', file: 'tests/test_zero_downtime_migration.py', category: 'backend' },
      ]
    },
    {
      name: 'Backend Integration Tests',
      status: 'pending',
      category: 'backend',
      icon: <Database className="h-4 w-4" />,
      tests: [
        { id: '46', name: 'System integration tests', status: 'pending', file: 'tests/integration/test_system_integration.py', category: 'backend' },
        { id: '47', name: 'API integration tests', status: 'pending', file: 'tests/integration/test_api_integration.py', category: 'backend' },
        { id: '48', name: 'User journey tests', status: 'pending', file: 'tests/integration/test_user_journey.py', category: 'backend' },
        { id: '49', name: 'Payment integration tests', status: 'pending', file: 'tests/integration/test_payment_integrations.py', category: 'backend' },
        { id: '50', name: 'Shipping integration tests', status: 'pending', file: 'tests/integration/test_shipping_integrations.py', category: 'backend' },
        { id: '51', name: 'Notification flows tests', status: 'pending', file: 'tests/integration/test_notification_flows.py', category: 'backend' },
        { id: '52', name: 'Migration workflow tests', status: 'pending', file: 'tests/integration/test_migration_workflow.py', category: 'backend' },
      ]
    },
    {
      name: 'Backend Performance & Security',
      status: 'pending',
      category: 'backend',
      icon: <Shield className="h-4 w-4" />,
      tests: [
        { id: '53', name: 'Load testing performance tests', status: 'pending', file: 'tests/performance/test_load_testing.py', category: 'backend' },
        { id: '54', name: 'Security vulnerability tests', status: 'pending', file: 'tests/security/test_security_vulnerabilities.py', category: 'backend' },
        { id: '55', name: 'Security hardening tests', status: 'pending', file: 'tests/security/test_security.py', category: 'backend' },
        { id: '56', name: 'Admin workflow E2E tests', status: 'pending', file: 'tests/e2e/test_admin_workflows.py', category: 'backend' },
        { id: '57', name: 'Workflow debugging E2E tests', status: 'pending', file: 'tests/e2e/test_workflow_debugging_e2e.py', category: 'backend' },
      ]
    },
    {
      name: 'QA Web Tests',
      status: 'pending',
      category: 'qa-web',
      icon: <Globe className="h-4 w-4" />,
      tests: [
        { id: '58', name: 'Authentication web tests', status: 'pending', file: 'qa-testing-framework/web/test_authentication.py', category: 'qa-web' },
        { id: '59', name: 'Product browsing web tests', status: 'pending', file: 'qa-testing-framework/web/test_product_browsing.py', category: 'qa-web' },
        { id: '60', name: 'Shopping cart checkout tests', status: 'pending', file: 'qa-testing-framework/web/test_shopping_cart_checkout.py', category: 'qa-web' },
        { id: '61', name: 'Payment processing web tests', status: 'pending', file: 'qa-testing-framework/web/test_payment_processing.py', category: 'qa-web' },
      ]
    },
    {
      name: 'QA API Tests',
      status: 'pending',
      category: 'qa-api',
      icon: <Server className="h-4 w-4" />,
      tests: [
        { id: '62', name: 'API authentication tests', status: 'pending', file: 'qa-testing-framework/api/test_authentication.py', category: 'qa-api' },
        { id: '63', name: 'API client tests', status: 'pending', file: 'qa-testing-framework/api/test_api_client.py', category: 'qa-api' },
        { id: '64', name: 'Product order management API tests', status: 'pending', file: 'qa-testing-framework/api/test_product_order_management.py', category: 'qa-api' },
        { id: '65', name: 'Payment transaction API tests', status: 'pending', file: 'qa-testing-framework/api/test_payment_transactions.py', category: 'qa-api' },
        { id: '66', name: 'Auth integration API tests', status: 'pending', file: 'qa-testing-framework/api/test_auth_integration.py', category: 'qa-api' },
        { id: '67', name: 'Product order integration tests', status: 'pending', file: 'qa-testing-framework/api/test_product_order_integration.py', category: 'qa-api' },
      ]
    },
    {
      name: 'QA Mobile Tests',
      status: 'pending',
      category: 'qa-mobile',
      icon: <Smartphone className="h-4 w-4" />,
      tests: [
        { id: '68', name: 'Mobile authentication tests', status: 'pending', file: 'qa-testing-framework/mobile/test_mobile_auth.py', category: 'qa-mobile' },
        { id: '69', name: 'Mobile shopping tests', status: 'pending', file: 'qa-testing-framework/mobile/test_mobile_shopping.py', category: 'qa-mobile' },
        { id: '70', name: 'Mobile auth integration tests', status: 'pending', file: 'qa-testing-framework/mobile/test_mobile_auth_integration.py', category: 'qa-mobile' },
      ]
    },
    {
      name: 'QA Database Tests',
      status: 'pending',
      category: 'qa-database',
      icon: <Database className="h-4 w-4" />,
      tests: [
        { id: '71', name: 'Database integration tests', status: 'pending', file: 'qa-testing-framework/tests/test_database_integration.py', category: 'qa-database' },
        { id: '72', name: 'Database connection tests', status: 'pending', file: 'qa-testing-framework/tests/test_database.py', category: 'qa-database' },
        { id: '73', name: 'Data manager tests', status: 'pending', file: 'qa-testing-framework/tests/test_data_manager.py', category: 'qa-database' },
        { id: '74', name: 'Database models tests', status: 'pending', file: 'qa-testing-framework/tests/test_models.py', category: 'qa-database' },
      ]
    }
  ];

  useEffect(() => {
    setTestSuites(mockTestSuites);
  }, []);

  const runTests = async (suiteFilter?: string) => {
    setIsRunning(true);
    setProgress(0);
    setLogs([]);
    
    const suitesToRun = suiteFilter && suiteFilter !== 'all' 
      ? testSuites.filter(suite => suite.name === suiteFilter)
      : testSuites;

    const totalTests = suitesToRun.reduce((acc, suite) => acc + suite.tests.length, 0);
    let completedTests = 0;

    // Simulate test execution
    for (const suite of suitesToRun) {
      setTestSuites(prev => prev.map(s => 
        s.name === suite.name ? { ...s, status: 'running' } : s
      ));

      setLogs(prev => [...prev, `Running ${suite.name}...`]);

      for (const test of suite.tests) {
        // Simulate test execution time
        await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500));
        
        // Randomly determine test result (in real implementation, this would be actual test results)
        const success = Math.random() > 0.2; // 80% success rate
        const duration = Math.random() * 500 + 100;
        
        const updatedTest: TestResult = {
          ...test,
          status: success ? 'passed' : 'failed',
          duration,
          error: success ? undefined : 'Test assertion failed: Expected true but received false'
        };

        setTestSuites(prev => prev.map(s => 
          s.name === suite.name 
            ? { 
                ...s, 
                tests: s.tests.map(t => t.id === test.id ? updatedTest : t)
              }
            : s
        ));

        completedTests++;
        setProgress((completedTests / totalTests) * 100);
        
        const status = success ? '✓' : '✗';
        setLogs(prev => [...prev, `  ${status} ${test.name} (${duration.toFixed(0)}ms)`]);
      }

      setTestSuites(prev => prev.map(s => 
        s.name === suite.name ? { ...s, status: 'completed' } : s
      ));
    }

    setIsRunning(false);
    setLogs(prev => [...prev, 'Test run completed!']);
  };

  const stopTests = () => {
    setIsRunning(false);
    setLogs(prev => [...prev, 'Test run stopped by user']);
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'passed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'skipped':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: TestResult['status']) => {
    const variants = {
      passed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      running: 'bg-blue-100 text-blue-800',
      skipped: 'bg-yellow-100 text-yellow-800',
      pending: 'bg-gray-100 text-gray-800'
    };

    return (
      <Badge className={variants[status]}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getTotalStats = () => {
    const allTests = testSuites.flatMap(suite => suite.tests);
    return {
      total: allTests.length,
      passed: allTests.filter(t => t.status === 'passed').length,
      failed: allTests.filter(t => t.status === 'failed').length,
      pending: allTests.filter(t => t.status === 'pending').length,
      running: allTests.filter(t => t.status === 'running').length
    };
  };

  const stats = getTotalStats();

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Test Runner</h1>
          <p className="text-gray-600 dark:text-gray-300">
            Run and monitor your comprehensive test suites across Frontend, Backend, and QA layers
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <select 
            value={selectedSuite}
            onChange={(e) => setSelectedSuite(e.target.value)}
            className="px-3 py-2 border rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600"
            disabled={isRunning}
          >
            <option value="all">All Test Suites ({testSuites.reduce((acc, suite) => acc + suite.tests.length, 0)} tests)</option>
            {testSuites.map(suite => (
              <option key={suite.name} value={suite.name}>
                {suite.name} ({suite.tests.length} tests)
              </option>
            ))}
          </select>
          
          {isRunning ? (
            <Button onClick={stopTests} variant="destructive">
              <Square className="h-4 w-4 mr-2" />
              Stop Tests
            </Button>
          ) : (
            <Button onClick={() => runTests(selectedSuite)}>
              <Play className="h-4 w-4 mr-2" />
              Run Tests
            </Button>
          )}
        </div>
      </div>

      {/* Progress and Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-blue-500" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Passed</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.passed}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-500" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Failed</p>
                <p className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.failed}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <RefreshCw className={`h-4 w-4 text-blue-500 ${stats.running > 0 ? 'animate-spin' : ''}`} />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Running</p>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.running}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Pending</p>
                <p className="text-2xl font-bold text-gray-600 dark:text-gray-300">{stats.pending}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Progress Bar */}
      {isRunning && (
        <Card>
          <CardContent className="p-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-700 dark:text-gray-300">
                <span>Test Progress</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="w-full" />
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="suites" className="space-y-4">
        <TabsList>
          <TabsTrigger value="suites">Test Suites</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="suites" className="space-y-4">
          {testSuites.map((suite) => (
            <Card key={suite.name}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-gray-100">
                    {suite.icon}
                    {suite.status === 'running' && (
                      <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />
                    )}
                    {suite.name}
                    <Badge className="ml-2 bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                      {suite.category.toUpperCase()}
                    </Badge>
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant={suite.status === 'completed' ? 'default' : 'secondary'}>
                      {suite.tests.filter(t => t.status === 'passed').length}/{suite.tests.length} passed
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {suite.tests.map((test) => (
                    <div key={test.id} className="flex items-center justify-between p-3 rounded border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(test.status)}
                        <div>
                          <p className="font-medium text-gray-900 dark:text-gray-100">{test.name}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400 font-mono">{test.file}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {test.duration && (
                          <span className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                            {test.duration.toFixed(0)}ms
                          </span>
                        )}
                        {getStatusBadge(test.status)}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-gray-100">
                <Terminal className="h-4 w-4" />
                Test Logs
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96 w-full rounded border border-gray-200 dark:border-gray-700 p-4 bg-gray-900 dark:bg-gray-950">
                <div className="space-y-1 font-mono text-sm">
                  {logs.length === 0 ? (
                    <p className="text-gray-400">No logs yet. Run tests to see output.</p>
                  ) : (
                    logs.map((log, index) => (
                      <div key={index} className="whitespace-pre-wrap text-green-400">
                        <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span> {log}
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}