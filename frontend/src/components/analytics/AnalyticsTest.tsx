'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Select } from '@/components/ui/Select';
import { DatePickerWithRange } from '@/components/ui/date-range-picker';

export default function AnalyticsTest() {
  const [dateRange, setDateRange] = React.useState({
    from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
    to: new Date()
  });

  const [selectedValue, setSelectedValue] = React.useState('test');

  return (
    <div className="p-6 space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Analytics Components Test</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="text-lg font-medium mb-2">Date Range Picker</h3>
            <DatePickerWithRange
              date={dateRange}
              onDateChange={setDateRange}
            />
          </div>

          <div>
            <h3 className="text-lg font-medium mb-2">Select Component</h3>
            <Select value={selectedValue} onChange={setSelectedValue}>
              <option value="test">Test Option</option>
              <option value="another">Another Option</option>
            </Select>
          </div>

          <div>
            <h3 className="text-lg font-medium mb-2">Other Components</h3>
            <div className="flex items-center space-x-2">
              <Button>Test Button</Button>
              <Badge>Test Badge</Badge>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium mb-2">Selected Values</h3>
            <p>Date Range: {dateRange.from.toLocaleDateString()} - {dateRange.to.toLocaleDateString()}</p>
            <p>Selected: {selectedValue}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}