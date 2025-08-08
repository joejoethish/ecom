'use client';

import React from 'react';
import { Card } from '@/components/ui/card';

interface FinancialKPIDashboardProps {
  className?: string;
  accountingPeriodId?: string;
}

export default function FinancialKPIDashboard({ className = '', accountingPeriodId }: FinancialKPIDashboardProps) {
  return (
    <div className={`space-y-6 ${className}`}>
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Financial KPI Dashboard</h2>
        <p className="text-gray-600">Financial KPIs and metrics will be displayed here.</p>
      </Card>
    </div>
  );
}