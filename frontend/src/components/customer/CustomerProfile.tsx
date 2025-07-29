'use client';

import { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/hooks/redux';
import { fetchCustomerProfile, updateCustomerProfile } from '@/store/slices/customerSlice';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import toast from 'react-hot-toast';

export function CustomerProfile() {
    const dispatch = useAppDispatch();
    const { user } = useAppSelector((state) => state.auth);
    const { profile, loading } = useAppSelector((state) => state.customer);

    const [formData, setFormData] = useState({
        date_of_birth: '',
        gender: '' as 'M' | 'F' | 'O' | '',
    });
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [isEditing, setIsEditing] = useState(false);

    useEffect(() => {
        dispatch(fetchCustomerProfile());
    }, [dispatch]);

    useEffect(() => {
        if (profile) {
            setFormData({
                date_of_birth: profile.date_of_birth || '',
                gender: profile.gender || '',
            });
        }
    }, [profile]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        // Clear error when user starts typing
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const validateForm = () => {
        const newErrors: Record<string, string> = {};

        // Date of birth validation (optional)
        if (formData.date_of_birth) {
            const birthDate = new Date(formData.date_of_birth);
            const today = new Date();
            const age = today.getFullYear() - birthDate.getFullYear();

            if (birthDate > today) {
                newErrors.date_of_birth = 'Date of birth cannot be in the future';
            } else if (age > 120) {
                newErrors.date_of_birth = 'Please enter a valid date of birth';
            }
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        try {
            await dispatch(updateCustomerProfile({
                ...formData,
                gender: formData.gender || undefined,
            })).unwrap();
            toast.success('Profile updated successfully!');
            setIsEditing(false);
        } catch (error: any) {
            toast.error(error || 'Failed to update profile');
        }
    };

    const handleCancel = () => {
        if (profile) {
            setFormData({
                date_of_birth: profile.date_of_birth || '',
                gender: profile.gender || '',
            });
        }
        setErrors({});
        setIsEditing(false);
    };

    const handleRefresh = async () => {
        try {
            await dispatch(fetchCustomerProfile()).unwrap();
            toast.success('Profile refreshed');
        } catch (error: any) {
            toast.error('Failed to refresh profile');
        }
    };

    if (!user) {
        return (
            <div className="text-center py-8">
                <p className="text-gray-500">No user data available</p>
            </div>
        );
    }

    return (
        <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold text-gray-900">Customer Profile</h2>
                    <div className="flex space-x-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleRefresh}
                            loading={loading}
                        >
                            Refresh
                        </Button>
                        {!isEditing && (
                            <Button
                                variant="primary"
                                size="sm"
                                onClick={() => setIsEditing(true)}
                            >
                                Edit Profile
                            </Button>
                        )}
                    </div>
                </div>
            </div>

            <div className="px-6 py-4">
                {!isEditing ? (
                    <div className="space-y-4">
                        {/* Basic User Info */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Username</label>
                                <p className="mt-1 text-sm text-gray-900">{user.username}</p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Email</label>
                                <p className="mt-1 text-sm text-gray-900">{user.email}</p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Phone Number</label>
                                <p className="mt-1 text-sm text-gray-900">{user.phone_number || 'Not provided'}</p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Account Type</label>
                                <p className="mt-1 text-sm text-gray-900 capitalize">{user.user_type}</p>
                            </div>
                        </div>

                        {/* Customer-specific Info */}
                        <div className="border-t pt-4 mt-4">
                            <h3 className="text-lg font-medium text-gray-900 mb-4">Additional Information</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Date of Birth</label>
                                    <p className="mt-1 text-sm text-gray-900">
                                        {profile?.date_of_birth
                                            ? new Date(profile.date_of_birth).toLocaleDateString()
                                            : 'Not provided'
                                        }
                                    </p>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Gender</label>
                                    <p className="mt-1 text-sm text-gray-900">
                                        {profile?.gender
                                            ? profile.gender === 'M' ? 'Male' : profile.gender === 'F' ? 'Female' : 'Other'
                                            : 'Not specified'
                                        }
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Account Status */}
                        <div className="border-t pt-4 mt-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Verification Status</label>
                                    <p className="mt-1 text-sm">
                                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${user.is_verified
                                            ? 'bg-green-100 text-green-800'
                                            : 'bg-yellow-100 text-yellow-800'
                                            }`}>
                                            {user.is_verified ? 'Verified' : 'Unverified'}
                                        </span>
                                    </p>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Member Since</label>
                                    <p className="mt-1 text-sm text-gray-900">
                                        {new Date(user.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <Input
                                label="Date of Birth"
                                name="date_of_birth"
                                type="date"
                                value={formData.date_of_birth}
                                onChange={handleChange}
                                error={errors.date_of_birth}
                            />
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Gender
                                </label>
                                <select
                                    name="gender"
                                    value={formData.gender}
                                    onChange={handleChange}
                                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                >
                                    <option value="">Select Gender</option>
                                    <option value="M">Male</option>
                                    <option value="F">Female</option>
                                    <option value="O">Other</option>
                                </select>
                            </div>
                        </div>

                        <div className="flex justify-end space-x-3 pt-4">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={handleCancel}
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                loading={loading}
                            >
                                Save Changes
                            </Button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}