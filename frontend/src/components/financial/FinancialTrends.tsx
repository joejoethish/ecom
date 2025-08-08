'use client';

import React from 'react';
import { Card } from '@/components/ui/card';

interface FinancialTrendsProps {
  className?: string;
  months?: number;
}

export default function FinancialTrends({ className = '', months }: FinancialTrendsProps) {
  return (
    <div className={`space-y-6 ${className}`}>
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Financial Trends</h2>
        <p className="text-gray-600">Financial trends analysis will be displayed here.</p>
      </Card>
    </div>
  );
}