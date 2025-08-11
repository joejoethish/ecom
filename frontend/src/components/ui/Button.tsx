import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: &apos;primary&apos; | &apos;secondary&apos; | &apos;outline&apos; | &apos;ghost&apos;;
  size?: &apos;sm&apos; | &apos;md&apos; | &apos;lg&apos;;
  loading?: boolean;
  children: React.ReactNode;
}

  variant = &apos;primary&apos;,
  size = &apos;md&apos;,
  loading = false,
  disabled,
  children,
  className = &apos;&apos;,
  ...props
}) => {
  const baseClasses = &apos;inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 touch-manipulation select-none&apos;;
  
  const variantClasses = {
    primary: &apos;bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 disabled:bg-blue-300&apos;,
    secondary: &apos;bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500 disabled:bg-gray-300&apos;,
    outline: &apos;border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400 disabled:border-gray-200&apos;,
    ghost: &apos;text-gray-700 hover:bg-gray-100 focus:ring-blue-500 disabled:text-gray-400 disabled:hover:bg-transparent&apos;
  };

  const sizeClasses = {
    sm: &apos;px-3 py-2 text-sm min-h-[36px]&apos;,
    md: &apos;px-4 py-2 text-sm min-h-[44px]&apos;,
    lg: &apos;px-6 py-3 text-base min-h-[48px]&apos;
  };

  const disabledClasses = &apos;disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none&apos;;

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${disabledClasses} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <div className="animate-spin w-4 h-4 border-2 border-current border-t-transparent rounded-full mr-2"></div>
      )}
      {children}
    </button>
  );
};

export default Button;
export { Button };