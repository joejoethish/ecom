'use client';

import React from 'react';
import { Card } from '@/components/ui/card';

interface CostCenterAnalysisProps {
  className?: string;
  startDate?: Date;
  endDate?: Date;
}

export default function CostCenterAnalysis({ className = '', startDate, endDate }: CostCenterAnalysisProps) {
  return (
    <div className={`space-y-6 ${className}`}>
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Cost Center Analysis</h2>
        <p className="text-gray-600">Cost center analysis will be displayed here.</p>
      </Card>
    </div>
  );
}