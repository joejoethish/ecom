'use client';

import { Calendar } from 'lucide-react';

interface DateRangePickerProps {
  from: string;
  to: string;
  onChange: (from: string, to: string) => void;
}

export default function DateRangePicker({ from, to, onChange }: DateRangePickerProps) {
  const handleFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value, to);
  };

  const handleToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(from, e.target.value);
  };

  const setPresetRange = (days: number) => {
    const toDate = new Date();
    const fromDate = new Date(toDate.getTime() - days * 24 * 60 * 60 * 1000);
    
    onChange(
      fromDate.toISOString().split(&apos;T&apos;)[0],
      toDate.toISOString().split(&apos;T&apos;)[0]
    );
  };

  return (
    <div className="flex items-center space-x-2">
      {/* Preset buttons */}
      <div className="flex space-x-1">
        <button
          onClick={() => setPresetRange(7)}
          className=&quot;px-3 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50&quot;
        >
          7D
        </button>
        <button
          onClick={() => setPresetRange(30)}
          className=&quot;px-3 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50&quot;
        >
          30D
        </button>
        <button
          onClick={() => setPresetRange(90)}
          className=&quot;px-3 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50&quot;
        >
          90D
        </button>
      </div>

      {/* Date inputs */}
      <div className="flex items-center space-x-2 border border-gray-300 rounded-md px-3 py-2 bg-white">
        <Calendar className="h-4 w-4 text-gray-400" />
        <input
          type="date"
          value={from}
          onChange={handleFromChange}
          className="text-sm border-none outline-none bg-transparent"
        />
        <span className="text-gray-400">to</span>
        <input
          type="date"
          value={to}
          onChange={handleToChange}
          className="text-sm border-none outline-none bg-transparent"
        />
      </div>
    </div>
  );
}