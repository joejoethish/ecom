import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import { DateRangePicker } from '@/components/ui/date-range-picker';

interface ProfitLossStatementProps {
  startDate?: Date;
  endDate?: Date;
  costCenterId?: string | null;
  className?: string;
}

interface PLLineItem {
  id: string;
  name: string;
  amount: number;
  percentage?: number;
  children?: PLLineItem[];
}

interface PLData {
  period: {
    start_date: string;
    end_date: string;
  };
  revenue: PLLineItem[];
  cost_of_goods_sold: PLLineItem[];
  operating_expenses: PLLineItem[];
  other_income: PLLineItem[];
  other_expenses: PLLineItem[];
  totals: {
    total_revenue: number;
    total_cogs: number;
    gross_profit: number;
    gross_margin: number;
    total_operating_expenses: number;
    operating_income: number;
    operating_margin: number;
    total_other_income: number;
    total_other_expenses: number;
    net_income: number;
    net_margin: number;
  };
}
const ProfitLossStatement: React.FC<ProfitLossStatementProps> = ({
  startDate,
  endDate,
  costCenterId,
  className = ''
}) => {
  const [plData, setPLData] = useState<PLData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState('current_month');
  const [showComparison, setShowComparison] = useState(false);
  const [dateRange, setDateRange] = useState({
    from: startDate || new Date(new Date().getFullYear(), new Date().getMonth(), 1),
    to: endDate || new Date()
  });

  // Mock data for development
  const mockPLData: PLData = {
    period: {
      start_date: '2024-01-01',
      end_date: '2024-01-31'
    },
    revenue: [
      {
        id: 'product_sales',
        name: 'Product Sales',
        amount: 1250000,
        percentage: 85.5,
        children: [
          { id: 'electronics', name: 'Electronics', amount: 750000 },
          { id: 'clothing', name: 'Clothing', amount: 300000 },
          { id: 'home_garden', name: 'Home & Garden', amount: 200000 }
        ]
      },
      {
        id: 'service_revenue',
        name: 'Service Revenue',
        amount: 150000,
        percentage: 10.3
      },
      {
        id: 'shipping_fees',
        name: 'Shipping Fees',
        amount: 62000,
        percentage: 4.2
      }
    ],
    cost_of_goods_sold: [
      {
        id: 'product_costs',
        name: 'Product Costs',
        amount: 750000,
        percentage: 60.0,
        children: [
          { id: 'inventory_costs', name: 'Inventory Costs', amount: 650000 },
          { id: 'shipping_costs', name: 'Shipping Costs', amount: 100000 }
        ]
      },
      {
        id: 'fulfillment_costs',
        name: 'Fulfillment Costs',
        amount: 85000,
        percentage: 6.8
      }
    ],
    operating_expenses: [
      {
        id: 'marketing',
        name: 'Marketing & Advertising',
        amount: 180000,
        percentage: 12.3
      },
      {
        id: 'personnel',
        name: 'Personnel Costs',
        amount: 220000,
        percentage: 15.1
      },
      {
        id: 'technology',
        name: 'Technology & Software',
        amount: 45000,
        percentage: 3.1
      },
      {
        id: 'facilities',
        name: 'Facilities & Utilities',
        amount: 35000,
        percentage: 2.4
      }
    ],
    other_income: [
      {
        id: 'interest_income',
        name: 'Interest Income',
        amount: 5000,
        percentage: 0.3
      }
    ],
    other_expenses: [
      {
        id: 'interest_expense',
        name: 'Interest Expense',
        amount: 12000,
        percentage: 0.8
      }
    ],
    totals: {
      total_revenue: 1462000,
      total_cogs: 835000,
      gross_profit: 627000,
      gross_margin: 42.9,
      total_operating_expenses: 480000,
      operating_income: 147000,
      operating_margin: 10.1,
      total_other_income: 5000,
      total_other_expenses: 12000,
      net_income: 140000,
      net_margin: 9.6
    }
  };

  useEffect(() => {
    fetchPLData();
  }, [dateRange, costCenterId]);

  const fetchPLData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setPLData(mockPLData);
    } catch (err) {
      setError('Failed to load P&L data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatPercentage = (percentage: number): string => {
    return `${percentage.toFixed(1)}%`;
  };

  const renderLineItem = (item: PLLineItem, level: number = 0, isTotal: boolean = false) => {
    const indentClass = level > 0 ? `pl-${level * 4}` : '';
    const fontWeight = isTotal ? 'font-bold' : level === 0 ? 'font-semibold' : 'font-normal';
    const borderClass = isTotal ? 'border-t-2 border-gray-300' : '';
    
    return (
      <React.Fragment key={item.id}>
        <tr className={`${borderClass} hover:bg-gray-50`}>
          <td className={`py-2 px-4 ${indentClass} ${fontWeight}`}>
            {item.name}
          </td>
          <td className={`py-2 px-4 text-right ${fontWeight}`}>
            {formatCurrency(item.amount)}
          </td>
          {item.percentage && (
            <td className={`py-2 px-4 text-right ${fontWeight} text-gray-600`}>
              {formatPercentage(item.percentage)}
            </td>
          )}
        </tr>
        {item.children?.map(child => renderLineItem(child, level + 1))}
      </React.Fragment>
    );
  };

  const renderSection = (title: string, items: PLLineItem[], total?: number, totalLabel?: string) => (
    <div className="mb-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-3 border-b border-gray-200 pb-2">
        {title}
      </h3>
      <table className="w-full">
        <tbody>
          {items.map(item => renderLineItem(item))}
          {total !== undefined && totalLabel && (
            <tr className="border-t-2 border-gray-300">
              <td className="py-2 px-4 font-bold">{totalLabel}</td>
              <td className="py-2 px-4 text-right font-bold">{formatCurrency(total)}</td>
              <td className="py-2 px-4"></td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );

  if (loading) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading P&L Statement...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center text-red-600">
          <p className="mb-4">{error}</p>
          <Button onClick={fetchPLData} variant="outline">
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  if (!plData) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center text-gray-600">
          <p>No P&L data available</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className={`p-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Profit & Loss Statement
          </h2>
          <p className="text-gray-600">
            Period: {new Date(plData.period.start_date).toLocaleDateString()} - {new Date(plData.period.end_date).toLocaleDateString()}
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 mt-4 lg:mt-0">
          <DateRangePicker
            date={dateRange}
            onDateChange={setDateRange}
            className="w-full sm:w-auto"
          />
          
          <Select
            value={selectedPeriod}
            onChange={(value) => setSelectedPeriod(value)}
            className="w-full sm:w-auto"
          >
            <option value="current_month">Current Month</option>
            <option value="last_month">Last Month</option>
            <option value="current_quarter">Current Quarter</option>
            <option value="last_quarter">Last Quarter</option>
            <option value="current_year">Current Year</option>
            <option value="last_year">Last Year</option>
            <option value="custom">Custom Range</option>
          </Select>
          
          <Button
            onClick={() => setShowComparison(!showComparison)}
            variant={showComparison ? "primary" : "outline"}
            className="w-full sm:w-auto"
          >
            {showComparison ? 'Hide' : 'Show'} Comparison
          </Button>
        </div>
      </div>

      {/* Key Metrics Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-blue-800 mb-1">Total Revenue</h4>
          <p className="text-2xl font-bold text-blue-900">{formatCurrency(plData.totals.total_revenue)}</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-green-800 mb-1">Gross Profit</h4>
          <p className="text-2xl font-bold text-green-900">{formatCurrency(plData.totals.gross_profit)}</p>
          <p className="text-sm text-green-700">{formatPercentage(plData.totals.gross_margin)} margin</p>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-purple-800 mb-1">Operating Income</h4>
          <p className="text-2xl font-bold text-purple-900">{formatCurrency(plData.totals.operating_income)}</p>
          <p className="text-sm text-purple-700">{formatPercentage(plData.totals.operating_margin)} margin</p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-gray-800 mb-1">Net Income</h4>
          <p className={`text-2xl font-bold ${plData.totals.net_income >= 0 ? 'text-green-900' : 'text-red-900'}`}>
            {formatCurrency(plData.totals.net_income)}
          </p>
          <p className="text-sm text-gray-700">{formatPercentage(plData.totals.net_margin)} margin</p>
        </div>
      </div>

      {/* Detailed P&L Statement */}
      <div className="space-y-6">
        {/* Revenue Section */}
        {renderSection('Revenue', plData.revenue, plData.totals.total_revenue, 'Total Revenue')}

        {/* Cost of Goods Sold Section */}
        {renderSection('Cost of Goods Sold', plData.cost_of_goods_sold, plData.totals.total_cogs, 'Total COGS')}

        {/* Gross Profit */}
        <div className="mb-6">
          <table className="w-full">
            <tbody>
              <tr className="border-t-2 border-gray-400 bg-green-50">
                <td className="py-3 px-4 font-bold text-green-800">Gross Profit</td>
                <td className="py-3 px-4 text-right font-bold text-green-800">
                  {formatCurrency(plData.totals.gross_profit)}
                </td>
                <td className="py-3 px-4 text-right font-bold text-green-700">
                  {formatPercentage(plData.totals.gross_margin)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Operating Expenses Section */}
        {renderSection('Operating Expenses', plData.operating_expenses, plData.totals.total_operating_expenses, 'Total Operating Expenses')}

        {/* Operating Income */}
        <div className="mb-6">
          <table className="w-full">
            <tbody>
              <tr className="border-t-2 border-gray-400 bg-purple-50">
                <td className="py-3 px-4 font-bold text-purple-800">Operating Income</td>
                <td className="py-3 px-4 text-right font-bold text-purple-800">
                  {formatCurrency(plData.totals.operating_income)}
                </td>
                <td className="py-3 px-4 text-right font-bold text-purple-700">
                  {formatPercentage(plData.totals.operating_margin)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Other Income/Expenses */}
        {plData.other_income.length > 0 && renderSection('Other Income', plData.other_income)}
        {plData.other_expenses.length > 0 && renderSection('Other Expenses', plData.other_expenses)}

        {/* Net Income */}
        <div className="mb-6">
          <table className="w-full">
            <tbody>
              <tr className={`border-t-4 ${plData.totals.net_income >= 0 ? 'border-green-400 bg-green-50' : 'border-red-400 bg-red-50'}`}>
                <td className={`py-4 px-4 font-bold text-xl ${plData.totals.net_income >= 0 ? 'text-green-800' : 'text-red-800'}`}>
                  Net Income
                </td>
                <td className={`py-4 px-4 text-right font-bold text-xl ${plData.totals.net_income >= 0 ? 'text-green-800' : 'text-red-800'}`}>
                  {formatCurrency(plData.totals.net_income)}
                </td>
                <td className={`py-4 px-4 text-right font-bold ${plData.totals.net_income >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {formatPercentage(plData.totals.net_margin)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Export Actions */}
      <div className="flex flex-wrap gap-2 pt-6 border-t border-gray-200">
        <Button variant="outline" size="sm">
          Export to PDF
        </Button>
        <Button variant="outline" size="sm">
          Export to Excel
        </Button>
        <Button variant="outline" size="sm">
          Email Report
        </Button>
        <Button variant="outline" size="sm">
          Schedule Report
        </Button>
      </div>
    </Card>
  );
};

export default ProfitLossStatement;