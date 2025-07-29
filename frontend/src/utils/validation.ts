// Validation utility functions

import { VALIDATION } from '@/constants';

export const validateEmail = (email: string): boolean => {
  return VALIDATION.EMAIL_REGEX.test(email);
};

export const validatePassword = (password: string): string[] => {
  const errors: string[] = [];
  
  if (password.length < VALIDATION.PASSWORD_MIN_LENGTH) {
    errors.push(`Password must be at least ${VALIDATION.PASSWORD_MIN_LENGTH} characters long`);
  }
  
  if (!/(?=.*[a-z])/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (!/(?=.*[A-Z])/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (!/(?=.*\d)/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  return errors;
};

export const validateUsername = (username: string): string[] => {
  const errors: string[] = [];
  
  if (username.length < VALIDATION.USERNAME_MIN_LENGTH) {
    errors.push(`Username must be at least ${VALIDATION.USERNAME_MIN_LENGTH} characters long`);
  }
  
  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    errors.push('Username can only contain letters, numbers, and underscores');
  }
  
  return errors;
};

export const validatePhone = (phone: string): boolean => {
  return VALIDATION.PHONE_REGEX.test(phone);
};

export const validateRequired = (value: string, fieldName: string): string | null => {
  if (!value || value.trim().length === 0) {
    return `${fieldName} is required`;
  }
  return null;
};

export const validatePasswordMatch = (password: string, confirmPassword: string): string | null => {
  if (password !== confirmPassword) {
    return 'Passwords do not match';
  }
  return null;
};

// Form validation helper
export const validateForm = (data: Record<string, any>, rules: Record<string, (value: any) => string | null>): Record<string, string> => {
  const errors: Record<string, string> = {};
  
  Object.keys(rules).forEach(field => {
    const error = rules[field](data[field]);
    if (error) {
      errors[field] = error;
    }
  });
  
  return errors;
};