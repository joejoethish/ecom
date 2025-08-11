import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  className = '',
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 touch-manipulation select-none';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 disabled:bg-blue-300',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500 disabled:bg-gray-300',
    outline: 'border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400 disabled:border-gray-200',
    ghost: 'text-gray-700 hover:bg-gray-100 focus:ring-blue-500 disabled:text-gray-400 disabled:hover:bg-transparent'
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm min-h-[36px]',
    md: 'px-4 py-2 text-sm min-h-[44px]',
    lg: 'px-6 py-3 text-base min-h-[48px]'
  };

  const disabledClasses = 'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none';

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