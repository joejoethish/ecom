'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useFormErrorHandling } from '@/hooks/useFormErrorHandling';

interface AdminLoginFormData {
    email: string;
    password: string;
}

export function AdminLoginForm() {
    const [formData, setFormData] = useState<AdminLoginFormData>({
        email: '',
        password: '',
    });

    const router = useRouter();

    const {
        fieldErrors,
        generalError,
        hasErrors,
        isSubmitting,
        handleError,
        handleSuccess,
        setSubmitting,
        handleFieldChange,
        getFieldError,
        clearErrors,
    } = useFormErrorHandling({
        showNotifications: true,
        clearOnChange: true,
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        handleFieldChange(name);
    };

    const validateForm = (): Record<string, string> => {
        const errors: Record<string, string> = {};

        if (!formData.email) {
            errors.email = 'Email is required';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            errors.email = 'Email is invalid';
        }

        if (!formData.password) {
            errors.password = 'Password is required';
        }

        return errors;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        clearErrors();

        const validationErrors = validateForm();
        if (Object.keys(validationErrors).length > 0) {
            // Set field errors
            Object.entries(validationErrors).forEach(([field, error]) => {
                // The error handling hook will manage these
            });
            return;
        }

        setSubmitting(true);

        try {
            console.log('Admin login attempt:', formData);
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));

            handleSuccess('Admin login successful!');
            router.push('/admin/dashboard');
        } catch (error: any) {
            handleError(error);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                        Admin Portal
                    </h2>
                    <p className="mt-2 text-center text-sm text-gray-600">
                        Sign in to access the admin dashboard
                    </p>
                </div>

                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    {/* Error Summary */}
                    {(hasErrors || generalError) && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                            <div className="flex items-start">
                                <div className="flex-1">
                                    <h3 className="text-sm font-medium text-red-800 mb-2">
                                        Please correct the following errors:
                                    </h3>

                                    {generalError && (
                                        <p className="text-sm text-red-700 mb-2">{generalError}</p>
                                    )}

                                    {Object.entries(fieldErrors).length > 0 && (
                                        <ul className="text-sm text-red-700 space-y-1">
                                            {Object.entries(fieldErrors).map(([field, error]) => (
                                                <li key={field} className="flex items-start">
                                                    <span className="inline-block w-2 h-2 bg-red-400 rounded-full mt-2 mr-2 flex-shrink-0" />
                                                    <span>
                                                        <strong className="capitalize">{field.replace('_', ' ')}:</strong> {error}
                                                    </span>
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="space-y-4">
                        <Input
                            label="Admin Email"
                            name="email"
                            type="email"
                            autoComplete="email"
                            required
                            value={formData.email}
                            onChange={handleChange}
                            error={getFieldError('email')}
                            placeholder="Enter your admin email"
                        />
                        <Input
                            label="Password"
                            name="password"
                            type="password"
                            autoComplete="current-password"
                            required
                            value={formData.password}
                            onChange={handleChange}
                            error={getFieldError('password')}
                            placeholder="Enter your password"
                        />
                    </div>

                    <div>
                        <Button
                            type="submit"
                            loading={isSubmitting}
                            className="w-full"
                            size="lg"
                            disabled={hasErrors}
                        >
                            Sign In to Admin Portal
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}