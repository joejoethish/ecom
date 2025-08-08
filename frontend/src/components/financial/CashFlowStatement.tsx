'use client';

import React from 'react';
import { Card } from '@/components/ui/card';

interface CashFlowStatementProps {
  className?: string;
  startDate?: Date;
  endDate?: Date;
}

export default function CashFlowStatement({ className = '', startDate, endDate }: CashFlowStatementProps) {
  return (
    <div className={`space-y-6 ${className}`}>
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Cash Flow Statement</h2>
        <p className="text-gray-600">Cash flow analysis will be displayed here.</p>
      </Card>
    </div>
  );
}