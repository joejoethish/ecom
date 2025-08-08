// Test file to verify financial components compile correctly
import React from 'react';
import ProfitLossStatement from './components/financial/ProfitLossStatement';

// This file tests that the ProfitLossStatement component can be imported and used
export default function TestFinancial() {
  return (
    <div>
      <ProfitLossStatement
        startDate={new Date('2024-01-01')}
        endDate={new Date('2024-01-31')}
        costCenterId={null}
      />
    </div>
  );
}