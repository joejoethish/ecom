import React from 'react';

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, &apos;onChange&apos;> {
  label?: string;
  error?: string;
  helperText?: string;
  children: React.ReactNode;
}

interface SelectTriggerProps {
  children: React.ReactNode;
  className?: string;
}

interface SelectContentProps {
  children: React.ReactNode;
}

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
}

interface SelectValueProps {
  placeholder?: string;
}

export function Select({
  label,
  error,
  helperText,
  className = &apos;&apos;,
  id,
  children,
  value,
  onChange,
  ...props
}: SelectProps & { 
  value?: string; 
  onChange?: (value: string) => void;
}) {
  const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;
  const errorId = error ? `${selectId}-error` : undefined;
  const helperId = helperText ? `${selectId}-helper` : undefined;
  
  const baseClasses = &apos;block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-0 sm:text-sm transition-colors touch-manipulation bg-white&apos;;
  const normalClasses = &apos;border-gray-300 focus:ring-blue-500 focus:border-blue-500 hover:border-gray-400&apos;;
  const errorClasses = &apos;border-red-300 focus:ring-red-500 focus:border-red-500&apos;;
  const disabledClasses = &apos;disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed disabled:border-gray-200&apos;;
  
  const selectClasses = `${baseClasses} ${error ? errorClasses : normalClasses} ${disabledClasses} ${className}`;
  
  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={selectId} className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={selectClasses}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={[errorId, helperId].filter(Boolean).join(' ') || undefined}
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        {...props}
      >
        {children}
      </select>
      {error && (
        <p id={errorId} className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={helperId} className="text-sm text-gray-500">
          {helperText}
        </p>
      )}
    </div>
  );
}

export function SelectTrigger({ children, className = &apos;&apos; }: SelectTriggerProps) {
  return <div className={className}>{children}</div>;
}

export function SelectContent({ children }: SelectContentProps) {
  return <>{children}</>;
}

export function SelectItem({ value, children }: SelectItemProps) {
  return <option value={value}>{children}</option>;
}

export function SelectValue({ placeholder }: SelectValueProps) {
  return <span>{placeholder}</span>;
}