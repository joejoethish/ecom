#!/usr/bin/env node

/**
 * Frontend Test Runner for E2E Workflow Debugging System
 * 
 * This script runs all frontend debugging system tests including:
 * - E2E workflow tests
 * - Component tests
 * - Integration tests
 * - Performance tests
 * 
 * Requirements: 4.1, 4.2, 4.3, 4.4, 7.1, 7.2, 7.3
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

class FrontendTestRunner {
  constructor() {
    this.startTime = new Date();
    this.results = {
      startTime: this.startTime.toISOString(),
      testSuites: {},
      summary: {},
      errors: []
    };
    
    // Test configuration
    this.testSuites = {
      'workflow-debugging-e2e': {
        path: 'src/__tests__/e2e/workflow-debugging.test.tsx',
        description: 'End-to-end workflow debugging tests',
        timeout: 300000, // 5 minutes
        required: true
      },
      'debugging-components': {
        path: 'src/__tests__/components/debugging/',
        description: 'Debugging component tests',
        timeout: 120000, // 2 minutes
        required: true
      },
      'debugging-services': {
        path: 'src/__tests__/services/debuggingApi.test.ts',
        description: 'Debugging service tests',
        timeout: 60000, // 1 minute
        required: true
      },
      'debugging-hooks': {
        path: 'src/__tests__/hooks/useCorrelationId.test.ts',
        description: 'Debugging hooks tests',
        timeout: 60000, // 1 minute
        required: false
      },
      'debugging-utils': {
        path: 'src/__tests__/utils/workflow-tracing.test.ts',
        description: 'Debugging utilities tests',
        timeout: 60000, // 1 minute
        required: false
      }
    };
    
    // Performance thresholds
    this.performanceThresholds = {
      testExecutionTime: 600000, // 10 minutes max
      memoryUsageMB: 512,        // 512MB max
      testFailureRate: 0.05      // 5% max failure rate
    };
  }
  
  async setupTestEnvironment() {
    console.log('🔧 Setting up frontend test environment...');
    
    try {
      // Check if node_modules exists
      if (!fs.existsSync('node_modules')) {
        console.log('  📦 Installing dependencies...');
        execSync('npm install', { stdio: 'inherit' });
      }
      
      // Check if test dependencies are available
      console.log('  🧪 Verifying test dependencies...');
      this.verifyTestDependencies();
      
      // Setup test database/mocks
      console.log('  🗄️  Setting up test mocks...');
      this.setupTestMocks();
      
      // Clear test cache
      console.log('  🧹 Clearing Jest cache...');
      try {
        execSync('npx jest --clearCache', { stdio: 'pipe' });
      } catch (e) {
        // Ignore cache clear errors
      }
      
      console.log('✅ Frontend test environment setup complete');
      return true;
      
    } catch (error) {
      console.error(`❌ Failed to setup test environment: ${error.message}`);
      this.results.errors.push(`Environment setup failed: ${error.message}`);
      return false;
    }
  }
  
  verifyTestDependencies() {
    const requiredDeps = [
      '@testing-library/react',
      '@testing-library/jest-dom',
      '@testing-library/user-event',
      'jest',
      'jest-environment-jsdom'
    ];
    
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    const allDeps = {
      ...packageJson.dependencies,
      ...packageJson.devDependencies
    };
    
    for (const dep of requiredDeps) {
      if (!allDeps[dep]) {
        throw new Error(`Missing required test dependency: ${dep}`);
      }
    }
  }
  
  setupTestMocks() {
    // Create test setup file if it doesn't exist
    const setupFile = 'src/setupTests.ts';
    if (!fs.existsSync(setupFile)) {
      const setupContent = `
import '@testing-library/jest-dom';

// Mock environment variables
process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
process.env.NEXT_PUBLIC_DEBUGGING_ENABLED = 'true';

// Mock fetch
global.fetch = jest.fn();

// Mock WebSocket
global.WebSocket = jest.fn().mockImplementation(() => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  send: jest.fn(),
  close: jest.fn(),
  readyState: 1
}));

// Mock performance API
Object.defineProperty(window, 'performance', {
  value: {
    now: jest.fn(() => Date.now()),
    mark: jest.fn(),
    measure: jest.fn(),
    getEntriesByType: jest.fn(() => []),
    getEntriesByName: jest.fn(() => [])
  }
});

// Mock intersection observer
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}));
`;
      fs.writeFileSync(setupFile, setupContent);
    }
  }
  
  async runTestSuite(suiteName, suiteConfig) {
    console.log(`\n🧪 Running ${suiteName}: ${suiteConfig.description}`);
    
    const suiteStartTime = Date.now();
    const suiteResults = {
      startTime: new Date().toISOString(),
      description: suiteConfig.description,
      status: 'running',
      testsRun: 0,
      failures: 0,
      errors: 0,
      skipped: 0,
      executionTime: 0,
      coverage: null,
      details: []
    };
    
    try {
      // Prepare Jest command
      const jestArgs = [
        '--testPathPattern=' + suiteConfig.path,
        '--verbose',
        '--coverage',
        '--coverageDirectory=coverage/' + suiteName,
        '--json',
        '--outputFile=test-results/' + suiteName + '.json'
      ];
      
      // Create test results directory
      if (!fs.existsSync('test-results')) {
        fs.mkdirSync('test-results', { recursive: true });
      }
      
      // Run Jest with timeout
      const result = await this.runWithTimeout(
        () => this.runJest(jestArgs),
        suiteConfig.timeout
      );
      
      if (result === null) {
        throw new Error(`Test suite timed out after ${suiteConfig.timeout / 1000} seconds`);
      }
      
      // Parse Jest results
      const jestResults = this.parseJestResults(suiteName);
      
      // Calculate metrics
      const suiteEndTime = Date.now();
      const executionTime = suiteEndTime - suiteStartTime;
      
      // Update results
      suiteResults.status = jestResults.success ? 'completed' : 'failed';
      suiteResults.testsRun = jestResults.numTotalTests;
      suiteResults.failures = jestResults.numFailedTests;
      suiteResults.errors = jestResults.numRuntimeErrorTestSuites;
      suiteResults.skipped = jestResults.numPendingTests;
      suiteResults.executionTime = executionTime;
      suiteResults.coverage = jestResults.coverageMap;
      suiteResults.endTime = new Date().toISOString();
      
      // Check performance thresholds
      this.checkSuitePerformance(suiteName, suiteResults);
      
      console.log(`✅ ${suiteName} completed in ${executionTime / 1000}s`);
      
    } catch (error) {
      if (error.message.includes('timed out')) {
        suiteResults.status = 'timeout';
        suiteResults.error = error.message;
        console.log(`⏰ ${suiteName} timed out`);
      } else {
        suiteResults.status = 'error';
        suiteResults.error = error.message;
        console.log(`❌ ${suiteName} failed: ${error.message}`);
      }
      suiteResults.endTime = new Date().toISOString();
    }
    
    this.results.testSuites[suiteName] = suiteResults;
    return suiteResults.status === 'completed';
  }
  
  async runJest(args) {
    return new Promise((resolve, reject) => {
      const jest = spawn('npx', ['jest', ...args], {
        stdio: 'inherit',
        shell: true
      });
      
      jest.on('close', (code) => {
        if (code === 0) {
          resolve(code);
        } else {
          reject(new Error(`Jest exited with code ${code}`));
        }
      });
      
      jest.on('error', (error) => {
        reject(error);
      });
    });
  }
  
  async runWithTimeout(func, timeout) {
    return Promise.race([
      func(),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Timeout')), timeout)
      )
    ]).catch(() => null);
  }
  
  parseJestResults(suiteName) {
    const resultsFile = `test-results/${suiteName}.json`;
    
    if (fs.existsSync(resultsFile)) {
      try {
        return JSON.parse(fs.readFileSync(resultsFile, 'utf8'));
      } catch (error) {
        console.warn(`⚠️  Could not parse Jest results for ${suiteName}`);
      }
    }
    
    // Return default results if file doesn't exist or can't be parsed
    return {
      success: false,
      numTotalTests: 0,
      numFailedTests: 0,
      numRuntimeErrorTestSuites: 0,
      numPendingTests: 0,
      coverageMap: null
    };
  }
  
  checkSuitePerformance(suiteName, suiteResults) {
    const warnings = [];
    
    // Check execution time (5 minutes max per suite)
    if (suiteResults.executionTime > 300000) {
      warnings.push(`Long execution time: ${suiteResults.executionTime / 1000}s`);
    }
    
    // Check failure rate
    if (suiteResults.testsRun > 0) {
      const failureRate = (suiteResults.failures + suiteResults.errors) / suiteResults.testsRun;
      if (failureRate > 0.1) { // 10% failure rate
        warnings.push(`High failure rate: ${(failureRate * 100).toFixed(1)}%`);
      }
    }
    
    if (warnings.length > 0) {
      suiteResults.performanceWarnings = warnings;
      console.log(`  ⚠️  Performance warnings for ${suiteName}:`);
      warnings.forEach(warning => console.log(`    - ${warning}`));
    }
  }
  
  async runLinting() {
    console.log('\n🔍 Running ESLint...');
    
    try {
      execSync('npx eslint src/ --ext .ts,.tsx --format json --output-file test-results/eslint.json', {
        stdio: 'pipe'
      });
      console.log('✅ ESLint passed');
      return true;
    } catch (error) {
      console.log('❌ ESLint failed');
      
      // Try to read ESLint results
      try {
        const eslintResults = JSON.parse(fs.readFileSync('test-results/eslint.json', 'utf8'));
        const errorCount = eslintResults.reduce((sum, file) => sum + file.errorCount, 0);
        const warningCount = eslintResults.reduce((sum, file) => sum + file.warningCount, 0);
        
        console.log(`  Errors: ${errorCount}, Warnings: ${warningCount}`);
        this.results.linting = { errors: errorCount, warnings: warningCount };
      } catch (parseError) {
        console.log('  Could not parse ESLint results');
      }
      
      return false;
    }
  }
  
  async runTypeChecking() {
    console.log('\n🔧 Running TypeScript type checking...');
    
    try {
      execSync('npx tsc --noEmit', { stdio: 'pipe' });
      console.log('✅ TypeScript type checking passed');
      return true;
    } catch (error) {
      console.log('❌ TypeScript type checking failed');
      console.log(error.stdout?.toString() || error.message);
      this.results.errors.push('TypeScript type checking failed');
      return false;
    }
  }
  
  async runBuildTest() {
    console.log('\n🏗️  Testing production build...');
    
    try {
      execSync('npm run build', { stdio: 'inherit' });
      console.log('✅ Production build successful');
      return true;
    } catch (error) {
      console.log('❌ Production build failed');
      this.results.errors.push('Production build failed');
      return false;
    }
  }
  
  generateTestReport() {
    const endTime = new Date();
    const totalExecutionTime = (endTime - this.startTime) / 1000;
    
    // Calculate summary statistics
    const totalTests = Object.values(this.results.testSuites)
      .reduce((sum, suite) => sum + (suite.testsRun || 0), 0);
    const totalFailures = Object.values(this.results.testSuites)
      .reduce((sum, suite) => sum + (suite.failures || 0), 0);
    const totalErrors = Object.values(this.results.testSuites)
      .reduce((sum, suite) => sum + (suite.errors || 0), 0);
    const totalSkipped = Object.values(this.results.testSuites)
      .reduce((sum, suite) => sum + (suite.skipped || 0), 0);
    
    const successRate = totalTests > 0 
      ? ((totalTests - totalFailures - totalErrors) / totalTests * 100) 
      : 0;
    
    this.results.endTime = endTime.toISOString();
    this.results.totalExecutionTime = totalExecutionTime;
    this.results.summary = {
      totalTests,
      totalFailures,
      totalErrors,
      totalSkipped,
      successRate,
      suitesPassed: Object.values(this.results.testSuites)
        .filter(suite => suite.status === 'completed').length,
      suitesFailed: Object.values(this.results.testSuites)
        .filter(suite => ['failed', 'error', 'timeout'].includes(suite.status)).length
    };
    
    // Generate report files
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const reportDir = 'test-reports';
    
    if (!fs.existsSync(reportDir)) {
      fs.mkdirSync(reportDir, { recursive: true });
    }
    
    const jsonReportPath = path.join(reportDir, `frontend-test-report-${timestamp}.json`);
    const htmlReportPath = path.join(reportDir, `frontend-test-report-${timestamp}.html`);
    
    // Write JSON report
    fs.writeFileSync(jsonReportPath, JSON.stringify(this.results, null, 2));
    
    // Generate HTML report
    this.generateHtmlReport(htmlReportPath);
    
    console.log(`\n📋 Test report generated: ${jsonReportPath}`);
    return jsonReportPath;
  }
  
  generateHtmlReport(reportPath) {
    const htmlTemplate = `
<!DOCTYPE html>
<html>
<head>
    <title>Frontend Debugging System - Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .metric { background: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; }
        .suite { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .passed { border-left: 5px solid #4CAF50; }
        .failed { border-left: 5px solid #f44336; }
        .warning { border-left: 5px solid #ff9800; }
        .error { color: #f44336; }
        .success { color: #4CAF50; }
        .coverage { background: #f9f9f9; padding: 10px; margin: 10px 0; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Frontend Debugging System - Test Report</h1>
        <p>Generated: ${this.results.endTime}</p>
        <p>Total Execution Time: ${this.results.totalExecutionTime.toFixed(2)} seconds</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Total Tests</h3>
            <p>${this.results.summary.totalTests}</p>
        </div>
        <div class="metric">
            <h3>Success Rate</h3>
            <p class="${this.results.summary.successRate > 90 ? 'success' : 'error'}">
                ${this.results.summary.successRate.toFixed(1)}%
            </p>
        </div>
        <div class="metric">
            <h3>Failures</h3>
            <p class="error">${this.results.summary.totalFailures}</p>
        </div>
        <div class="metric">
            <h3>Errors</h3>
            <p class="error">${this.results.summary.totalErrors}</p>
        </div>
    </div>
    
    <h2>Test Suites</h2>
    ${this.generateSuitesHtml()}
    
    ${this.generateErrorsHtml()}
</body>
</html>
    `;
    
    fs.writeFileSync(reportPath, htmlTemplate);
  }
  
  generateSuitesHtml() {
    return Object.entries(this.results.testSuites)
      .map(([suiteName, suiteData]) => {
        const statusClass = suiteData.status === 'completed' ? 'passed' : 'failed';
        
        return `
        <div class="suite ${statusClass}">
            <h3>${suiteName}</h3>
            <p>${suiteData.description}</p>
            <p>Status: <span class="${statusClass}">${suiteData.status}</span></p>
            <p>Tests Run: ${suiteData.testsRun || 0}</p>
            <p>Execution Time: ${((suiteData.executionTime || 0) / 1000).toFixed(2)}s</p>
            ${suiteData.coverage ? `
            <div class="coverage">
                <strong>Coverage:</strong> Available in coverage/${suiteName}/
            </div>
            ` : ''}
            ${suiteData.performanceWarnings ? `
            <div class="warning">
                <strong>Performance Warnings:</strong>
                <ul>
                    ${suiteData.performanceWarnings.map(w => `<li>${w}</li>`).join('')}
                </ul>
            </div>
            ` : ''}
        </div>
        `;
      }).join('');
  }
  
  generateErrorsHtml() {
    if (this.results.errors.length === 0) return '';
    
    return `
    <h2>Errors</h2>
    <ul>
        ${this.results.errors.map(error => `<li class="error">${error}</li>`).join('')}
    </ul>
    `;
  }
  
  async runAllTests() {
    console.log('🚀 Starting Frontend Debugging System Test Suite');
    console.log(`📅 Start time: ${this.startTime}`);
    
    // Setup test environment
    if (!(await this.setupTestEnvironment())) {
      return false;
    }
    
    let overallSuccess = true;
    
    // Run linting
    const lintSuccess = await this.runLinting();
    if (!lintSuccess) overallSuccess = false;
    
    // Run type checking
    const typeSuccess = await this.runTypeChecking();
    if (!typeSuccess) overallSuccess = false;
    
    // Run test suites
    for (const [suiteName, suiteConfig] of Object.entries(this.testSuites)) {
      const success = await this.runTestSuite(suiteName, suiteConfig);
      
      if (!success && suiteConfig.required) {
        overallSuccess = false;
        console.log(`❌ Required test suite ${suiteName} failed`);
      }
    }
    
    // Run build test
    const buildSuccess = await this.runBuildTest();
    if (!buildSuccess) overallSuccess = false;
    
    // Generate report
    const reportPath = this.generateTestReport();
    
    // Print summary
    console.log('\n' + '='.repeat(60));
    console.log('📊 FRONTEND TEST SUMMARY');
    console.log('='.repeat(60));
    console.log(`Total Tests: ${this.results.summary.totalTests}`);
    console.log(`Success Rate: ${this.results.summary.successRate.toFixed(1)}%`);
    console.log(`Failures: ${this.results.summary.totalFailures}`);
    console.log(`Errors: ${this.results.summary.totalErrors}`);
    console.log(`Execution Time: ${this.results.totalExecutionTime.toFixed(2)}s`);
    
    if (overallSuccess) {
      console.log('\n✅ ALL FRONTEND TESTS PASSED!');
    } else {
      console.log('\n❌ SOME FRONTEND TESTS FAILED!');
    }
    
    console.log(`\n📋 Detailed report: ${reportPath}`);
    
    return overallSuccess;
  }
}

// Main execution
async function main() {
  const args = process.argv.slice(2);
  const suite = args.find(arg => arg.startsWith('--suite='))?.split('=')[1];
  const skipLinting = args.includes('--skip-linting');
  const skipBuild = args.includes('--skip-build');
  
  const runner = new FrontendTestRunner();
  
  if (suite) {
    // Run specific suite only
    if (runner.testSuites[suite]) {
      await runner.setupTestEnvironment();
      const success = await runner.runTestSuite(suite, runner.testSuites[suite]);
      runner.generateTestReport();
      process.exit(success ? 0 : 1);
    } else {
      console.error(`❌ Unknown test suite: ${suite}`);
      console.error(`Available suites: ${Object.keys(runner.testSuites).join(', ')}`);
      process.exit(1);
    }
  } else {
    // Run all tests
    const success = await runner.runAllTests();
    process.exit(success ? 0 : 1);
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error('❌ Test runner error:', error);
    process.exit(1);
  });
}

module.exports = FrontendTestRunner;