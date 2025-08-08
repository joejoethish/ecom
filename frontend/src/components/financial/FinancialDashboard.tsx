import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { DateRangePicker } from '@/components/ui/date-range-picker';
import ProfitLossStatement from './ProfitLossStatement';
import BudgetVarianceReport from './BudgetVarianceReport';
import FinancialKPIDashboard from './FinancialKPIDashboard';
import CashFlowStatement from './CashFlowStatement';
import CostCenterAnalysis from './CostCenterAnalysis';
import FinancialTrends from './FinancialTrends';

interface FinancialDashboardProps {
  className?: string;
}

interface DashboardSummary {
  current_period: {
    id: string;
    name: string;
    start_date: string;
    end_date: string;
  };
  profit_loss: {
    revenue?: {
      total?: number;
    };
    net_income?: {
      amount?: number;
      margin_percentage?: number;
    };
  };
  kpis: {
    kpis?: Record<string, number | string>;
  };
  trends: {
    data?: Array<{
      period: string;
      value: number;
    }>;
  };
}

const FinancialDashboard: React.FC<FinancialDashboardProps> = ({ className = '' }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [dateRange, setDateRange] = useState({
    from: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
    to: new Date()
  });
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [dashboardData, setDashboardData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'profit-loss', label: 'P&L Statement', icon: '💰' },
    { id: 'budget-variance', label: 'Budget Variance', icon: '📈' },
    { id: 'cash-flow', label: 'Cash Flow', icon: '💸' },
    { id: 'kpis', label: 'KPIs', icon: '🎯' },
    { id: 'cost-centers', label: 'Cost Centers', icon: '🏢' },
    { id: 'trends', label: 'Trends', icon: '📉' }
  ];

  useEffect(() => {
    fetchDashboardSummary();
  }, []);

  const fetchDashboardSummary = async () => {
    try {
      setLoading(true);
      // Mock API call - replace with actual API
      const response = await fetch('/api/financial/analytics/dashboard_summary/');
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
        setSelectedPeriod(data.current_period.id);
      }
    } catch (error) {
      console.error('Error fetching dashboard summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportReport = async (reportType: string) => {
    try {
      const response = await fetch('/api/financial/analytics/export_report/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          report_type: reportType,
          name: `${reportType}_report_${new Date().toISOString().split('T')[0]}`,
          start_date: dateRange.from.toISOString().split('T')[0],
          end_date: dateRange.to.toISOString().split('T')[0],
          accounting_period_id: selectedPeriod,
          parameters: {}
        })
      });

      if (response.ok) {
        const data = await response.json();
        // Handle download
        window.open(data.download_url, '_blank');
      }
    } catch (error) {
      console.error('Error exporting report:', error);
    }
  };

  if (loading) {
    return (
      <div className={`financial-dashboard ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2">Loading financial data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`financial-dashboard ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Financial Analytics</h1>
            <p className="text-gray-600">
              Comprehensive financial reporting and analysis dashboard
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => handleExportReport('profit_loss')}
              className="bg-green-600 hover:bg-green-700"
            >
              📄 Export P&L
            </Button>
            <Button
              onClick={() => handleExportReport('budget_variance')}
              className="bg-blue-600 hover:bg-blue-700"
            >
              📊 Export Budget Report
            </Button>
          </div>
        </div>

        {/* Controls */}
        <div className="flex gap-4 items-center">
          <DateRangePicker
            date={dateRange}
            onDateChange={setDateRange}
            className="w-64"
          />
          <Select
            value={selectedPeriod}
            onChange={(value) => setSelectedPeriod(value)}
            className="w-48"
          >
            <option value="">Select Period</option>
            {dashboardData && (
              <option value={dashboardData.current_period.id}>
                {dashboardData.current_period.name}
              </option>
            )}
          </Select>
          <Button
            onClick={fetchDashboardSummary}
            className="bg-gray-600 hover:bg-gray-700"
          >
            🔄 Refresh
          </Button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && dashboardData && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Quick Stats */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Current Period Summary</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Period:</span>
                  <span className="font-medium">{dashboardData.current_period.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Revenue:</span>
                  <span className="font-medium text-green-600">
                    ${dashboardData.profit_loss.revenue?.total?.toLocaleString() || '0'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Net Income:</span>
                  <span className="font-medium text-blue-600">
                    ${dashboardData.profit_loss.net_income?.amount?.toLocaleString() || '0'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Net Margin:</span>
                  <span className="font-medium">
                    {dashboardData.profit_loss.net_income?.margin_percentage?.toFixed(1) || '0'}%
                  </span>
                </div>
              </div>
            </Card>

            {/* KPI Overview */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Key Performance Indicators</h3>
              <div className="space-y-3">
                {dashboardData.kpis?.kpis && Object.entries(dashboardData.kpis.kpis).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600 capitalize">
                      {key.replace('_', ' ')}:
                    </span>
                    <span className="font-medium">
                      {typeof value === 'number' ? `${value.toFixed(2)}%` : value}
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Recent Trends Chart Placeholder */}
            <Card className="p-6 lg:col-span-2">
              <h3 className="text-lg font-semibold mb-4">Financial Trends (Last 6 Months)</h3>
              <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <div className="text-4xl mb-2">📈</div>
                  <p>Trends chart will be displayed here</p>
                  <p className="text-sm">Install chart library to view interactive charts</p>
                </div>
              </div>
            </Card>
          </div>
        )}

        {activeTab === 'profit-loss' && (
          <ProfitLossStatement
            startDate={dateRange.from}
            endDate={dateRange.to}
            costCenterId={null}
          />
        )}

        {activeTab === 'budget-variance' && (
          <BudgetVarianceReport
            accountingPeriodId={selectedPeriod}
          />
        )}

        {activeTab === 'cash-flow' && (
          <CashFlowStatement
            startDate={dateRange.from}
            endDate={dateRange.to}
          />
        )}

        {activeTab === 'kpis' && (
          <FinancialKPIDashboard
            accountingPeriodId={selectedPeriod}
          />
        )}

        {activeTab === 'cost-centers' && (
          <CostCenterAnalysis
            startDate={dateRange.from}
            endDate={dateRange.to}
          />
        )}

        {activeTab === 'trends' && (
          <FinancialTrends months={12} />
        )}
      </div>
    </div>
  );
};

export default FinancialDashboard;