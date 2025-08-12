import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/progress';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { Play, Square as Stop, Download, History, TrendingUp, AlertTriangle } from 'lucide-react';

interface LoadTestConfig {
  url: string;
  concurrent_users: number;
  duration: number;
  ramp_up_time: number;
  method: string;
}

interface LoadTestResult {
  id: string;
  name: string;
  status: 'running' | 'completed' | 'failed';
  config: LoadTestConfig;
  results?: {
    summary: {
      total_requests: number;
      successful_requests: number;
      failed_requests: number;
      success_rate: number;
    };
    response_times: {
      min: number;
      max: number;
      avg: number;
      p95: number;
      p99: number;
    };
    throughput: {
      requests_per_second: number;
    };
  };
  started_at: string;
  completed_at?: string;
}

const LoadTestingPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState('configure');
  const [testConfig, setTestConfig] = useState<LoadTestConfig>({
    url: 'http://localhost:8000/api/',
    concurrent_users: 10,
    duration: 60,
    ramp_up_time: 10,
    method: 'GET'
  });
  const [currentTest, setCurrentTest] = useState<LoadTestResult | null>(null);
  const [testHistory, setTestHistory] = useState<LoadTestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    fetchTestHistory();
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRunning && currentTest) {
      interval = setInterval(() => {
        setProgress(prev => Math.min(prev + 1, 100));
        // In real implementation, this would poll the backend for test status
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning, currentTest]);

  const fetchTestHistory = async () => {
    try {
      const response = await fetch('/api/admin/performance/load-tests/');
      const data = await response.json();
      setTestHistory(data.results || []);
    } catch (error) {
      console.error('Failed to fetch test history:', error);
    }
  };

  const startLoadTest = async () => {
    try {
      setIsRunning(true);
      setProgress(0);
      
      const response = await fetch('/api/admin/performance/load-tests/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: `Load Test - ${new Date().toISOString()}`,
          config: testConfig
        })
      });

      const testResult = await response.json();
      setCurrentTest(testResult);
      
      // Simulate test completion after duration
      setTimeout(() => {
        setIsRunning(false);
        setProgress(100);
        fetchTestHistory();
      }, testConfig.duration * 1000);

    } catch (error) {
      console.error('Failed to start load test:', error);
      setIsRunning(false);
    }
  };

  const stopLoadTest = async () => {
    if (currentTest) {
      try {
        await fetch(`/api/admin/performance/load-tests/${currentTest.id}/stop/`, {
          method: 'POST'
        });
        setIsRunning(false);
        setCurrentTest(null);
      } catch (error) {
        console.error('Failed to stop load test:', error);
      }
    }
  };

  const exportResults = (test: LoadTestResult) => {
    const dataStr = JSON.stringify(test, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `load-test-${test.id}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const renderConfigurationTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Test Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="url">Target URL</Label>
              <Input
                id="url"
                value={testConfig.url}
                onChange={(e) => setTestConfig({...testConfig, url: e.target.value})}
                placeholder="http://localhost:8000/api/"
              />
            </div>
            <div>
              <Label htmlFor="method">HTTP Method</Label>
              <Select value={testConfig.method} onChange={(value: string) => setTestConfig({...testConfig, method: value})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="GET">GET</SelectItem>
                  <SelectItem value="POST">POST</SelectItem>
                  <SelectItem value="PUT">PUT</SelectItem>
                  <SelectItem value="DELETE">DELETE</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="users">Concurrent Users</Label>
              <Input
                id="users"
                type="number"
                value={testConfig.concurrent_users}
                onChange={(e) => setTestConfig({...testConfig, concurrent_users: parseInt(e.target.value)})}
                min="1"
                max="1000"
              />
            </div>
            <div>
              <Label htmlFor="duration">Duration (seconds)</Label>
              <Input
                id="duration"
                type="number"
                value={testConfig.duration}
                onChange={(e) => setTestConfig({...testConfig, duration: parseInt(e.target.value)})}
                min="10"
                max="3600"
              />
            </div>
            <div>
              <Label htmlFor="rampup">Ramp-up Time (seconds)</Label>
              <Input
                id="rampup"
                type="number"
                value={testConfig.ramp_up_time}
                onChange={(e) => setTestConfig({...testConfig, ramp_up_time: parseInt(e.target.value)})}
                min="1"
                max="300"
              />
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button 
              onClick={startLoadTest} 
              disabled={isRunning}
              className="flex items-center gap-2"
            >
              <Play className="h-4 w-4" />
              Start Load Test
            </Button>
            {isRunning && (
              <Button 
                onClick={stopLoadTest} 
                variant="outline"
                className="flex items-center gap-2"
              >
                <Stop className="h-4 w-4" />
                Stop Test
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {isRunning && (
        <Card>
          <CardHeader>
            <CardTitle>Test Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} />
              <div className="text-sm text-muted-foreground">
                Running for {Math.floor(progress * testConfig.duration / 100)} seconds
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderResultsTab = () => (
    <div className="space-y-6">
      {currentTest?.results && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Total Requests</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{currentTest.results.summary.total_requests}</div>
              <div className="text-sm text-muted-foreground">
                {currentTest.results.summary.successful_requests} successful
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Success Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{currentTest.results.summary.success_rate.toFixed(1)}%</div>
              <div className="text-sm text-muted-foreground">
                {currentTest.results.summary.failed_requests} failed
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Avg Response Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{currentTest.results.response_times.avg.toFixed(0)}ms</div>
              <div className="text-sm text-muted-foreground">
                P95: {currentTest.results.response_times.p95.toFixed(0)}ms
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {currentTest?.results && (
        <Card>
          <CardHeader>
            <CardTitle>Response Time Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[
                { name: 'Min', value: currentTest.results.response_times.min },
                { name: 'Avg', value: currentTest.results.response_times.avg },
                { name: 'P95', value: currentTest.results.response_times.p95 },
                { name: 'P99', value: currentTest.results.response_times.p99 },
                { name: 'Max', value: currentTest.results.response_times.max },
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => [`${Number(value).toFixed(0)}ms`, 'Response Time']} />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderHistoryTab = () => (
    <div className="space-y-4">
      {testHistory.map((test) => (
        <Card key={test.id}>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-lg">{test.name}</CardTitle>
                <div className="text-sm text-muted-foreground">
                  {new Date(test.started_at).toLocaleString()}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={test.status === 'completed' ? 'default' : test.status === 'failed' ? 'outline' : 'secondary'}>
                  {test.status}
                </Badge>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => exportResults(test)}
                  className="flex items-center gap-1"
                >
                  <Download className="h-3 w-3" />
                  Export
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="font-medium">Users</div>
                <div>{test.config.concurrent_users}</div>
              </div>
              <div>
                <div className="font-medium">Duration</div>
                <div>{test.config.duration}s</div>
              </div>
              {test.results && (
                <>
                  <div>
                    <div className="font-medium">Requests</div>
                    <div>{test.results.summary.total_requests}</div>
                  </div>
                  <div>
                    <div className="font-medium">Avg Response</div>
                    <div>{test.results.response_times.avg.toFixed(0)}ms</div>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Load Testing</h2>
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Performance Testing</span>
        </div>
      </div>

      <Tabs defaultValue={activeTab}>
        <TabsList>
          <TabsTrigger value="configure">Configure</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="configure">
          {renderConfigurationTab()}
        </TabsContent>

        <TabsContent value="results">
          {renderResultsTab()}
        </TabsContent>

        <TabsContent value="history">
          {renderHistoryTab()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default LoadTestingPanel;