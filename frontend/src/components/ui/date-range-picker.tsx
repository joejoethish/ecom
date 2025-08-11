'use client';

import React from 'react';

interface DateRange {
  from: Date;
  to: Date;
}

interface DatePickerWithRangeProps {
  date: DateRange;
  onDateChange: (range: DateRange) => void;
  className?: string;
}

export function DatePickerWithRange({ date, onDateChange, className = &apos;&apos; }: DatePickerWithRangeProps) {
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <input
        type="date"
        value={date.from.toISOString().split('T')[0]}
        onChange={(e) => onDateChange({ ...date, from: new Date(e.target.value) })}
        className=&quot;px-3 py-2 border rounded-md&quot;
      />
      <span className="text-sm text-gray-500">to</span>
      <input
        type="date"
        value={date.to.toISOString().split('T')[0]}
        onChange={(e) => onDateChange({ ...date, to: new Date(e.target.value) })}
        className=&quot;px-3 py-2 border rounded-md&quot;
      />
    </div>
  );
}

// Export as DateRangePicker for backward compatibility
export const DateRangePicker = DatePickerWithRange;