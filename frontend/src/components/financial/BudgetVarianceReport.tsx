'use client';

import React from 'react';
import { Card } from '@/components/ui/card';

interface BudgetVarianceReportProps {
  className?: string;
  accountingPeriodId?: string;
}

export default function BudgetVarianceReport({ className = '', accountingPeriodId }: BudgetVarianceReportProps) {
  return (
    <div className={`space-y-6 ${className}`}>
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Budget Variance Report</h2>
        <p className="text-gray-600">Budget variance analysis will be displayed here.</p>
      </Card>
    </div>
  );
}