'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { 
  User, 
  Mail, 
  Lock, 
  Phone, 
  UserPlus, 
  LogIn, 
  Key,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';
import toast from 'react-hot-toast';

interface AuthResponse {
  success: boolean;
  data?: any;
  error?: string;
}

export default function AuthDemoPage() {
  const [activeTab, setActiveTab] = useState('register');
  const [loading, setLoading] = useState(false);
  const [authStatus, setAuthStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [authMessage, setAuthMessage] = useState('');
  const [userToken, setUserToken] = useState<string | null>(null);

  // Registration form state
  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    phone_number: '',
    user_type: 'customer'
  });

  // Login form state
  const [loginForm, setLoginForm] = useState({
    email: '',
    password: ''
  });

  // Forgot password form state
  const [forgotPasswordForm, setForgotPasswordForm] = useState({
    email: ''
  });

  const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAuthStatus('idle');

    try {
      const response = await fetch(`${API_BASE_URL}/auth/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registerForm),
      });

      const data = await response.json();

      if (response.ok) {
        setAuthStatus('success');
        setAuthMessage('Registration successful!');
        setUserToken(data.tokens?.access || null);
        toast.success('Registration successful!');
        
        // Clear form
        setRegisterForm({
          username: '',
          email: '',
          password: '',
          password_confirm: '',
          phone_number: '',
          user_type: 'customer'
        });
      } else {
        setAuthStatus('error');
        setAuthMessage(data.error || 'Registration failed');
        toast.error(data.error || 'Registration failed');
      }
    } catch (error) {
      setAuthStatus('error');
      setAuthMessage('Network error. Please check if the backend server is running.');
      toast.error('Network error. Please check if the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAuthStatus('idle');

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginForm),
      });

      const data = await response.json();

      if (response.ok) {
        setAuthStatus('success');
        setAuthMessage('Login successful!');
        setUserToken(data.access || null);
        toast.success('Login successful!');
        
        // Clear form
        setLoginForm({
          email: '',
          password: ''
        });
      } else {
        setAuthStatus('error');
        setAuthMessage(data.error || 'Login failed');
        toast.error(data.error || 'Login failed');
      }
    } catch (error) {
      setAuthStatus('error');
      setAuthMessage('Network error. Please check if the backend server is running.');
      toast.error('Network error. Please check if the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAuthStatus('idle');

    try {
      const response = await fetch(`${API_BASE_URL}/auth/forgot-password/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(forgotPasswordForm),
      });

      const data = await response.json();

      if (response.ok) {
        setAuthStatus('success');
        setAuthMessage('Password reset email sent!');
        toast.success('Password reset email sent!');
        
        // Clear form
        setForgotPasswordForm({
          email: ''
        });
      } else {
        setAuthStatus('error');
        setAuthMessage(data.error || 'Failed to send reset email');
        toast.error(data.error || 'Failed to send reset email');
      }
    } catch (error) {
      setAuthStatus('error');
      setAuthMessage('Network error. Please check if the backend server is running.');
      toast.error('Network error. Please check if the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  const testProtectedEndpoint = async () => {
    if (!userToken) {
      toast.error('Please login first');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/profile/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok) {
        toast.success('Profile fetched successfully!');
        setAuthMessage(`Profile: ${data.username} (${data.email})`);
      } else {
        toast.error('Failed to fetch profile');
        setAuthMessage('Failed to fetch profile');
      }
    } catch (error) {
      toast.error('Network error');
      setAuthMessage('Network error');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = () => {
    switch (authStatus) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-blue-500" />;
    }
  };

  const getStatusColor = () => {
    switch (authStatus) {
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Authentication Demo
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Test the complete authentication workflow including registration, login, and password reset.
        </p>
      </div>

      {/* Status Display */}
      {authMessage && (
        <Card className={`mb-6 border ${getStatusColor()}`}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <span className="font-medium">{authMessage}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Token Display */}
      {userToken && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              Authentication Token
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded font-mono text-sm break-all">
              {userToken}
            </div>
            <Button 
              onClick={testProtectedEndpoint} 
              className="mt-3"
              disabled={loading}
            >
              Test Protected Endpoint
            </Button>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="register">Register</TabsTrigger>
          <TabsTrigger value="login">Login</TabsTrigger>
          <TabsTrigger value="forgot">Forgot Password</TabsTrigger>
        </TabsList>

        <TabsContent value="register">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserPlus className="h-5 w-5" />
                User Registration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Username"
                    type="text"
                    value={registerForm.username}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, username: e.target.value }))}
                    placeholder="Enter username"
                    required
                  />
                  <Input
                    label="Email"
                    type="email"
                    value={registerForm.email}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, email: e.target.value }))}
                    placeholder="Enter email"
                    required
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Password"
                    type="password"
                    value={registerForm.password}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, password: e.target.value }))}
                    placeholder="Enter password"
                    required
                  />
                  <Input
                    label="Confirm Password"
                    type="password"
                    value={registerForm.password_confirm}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, password_confirm: e.target.value }))}
                    placeholder="Confirm password"
                    required
                  />
                </div>

                <Input
                  label="Phone Number (Optional)"
                  type="tel"
                  value={registerForm.phone_number}
                  onChange={(e) => setRegisterForm(prev => ({ ...prev, phone_number: e.target.value }))}
                  placeholder="+1234567890"
                />

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    User Type
                  </label>
                  <select
                    value={registerForm.user_type}
                    onChange={(e) => setRegisterForm(prev => ({ ...prev, user_type: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="customer">Customer</option>
                    <option value="seller">Seller</option>
                  </select>
                </div>

                <Button type="submit" loading={loading} className="w-full">
                  Register
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="login">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LogIn className="h-5 w-5" />
                User Login
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleLogin} className="space-y-4">
                <Input
                  label="Email"
                  type="email"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="Enter email"
                  required
                />
                
                <Input
                  label="Password"
                  type="password"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
                  placeholder="Enter password"
                  required
                />

                <Button type="submit" loading={loading} className="w-full">
                  Login
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="forgot">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                Forgot Password
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleForgotPassword} className="space-y-4">
                <Input
                  label="Email"
                  type="email"
                  value={forgotPasswordForm.email}
                  onChange={(e) => setForgotPasswordForm(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="Enter your email"
                  required
                />

                <Button type="submit" loading={loading} className="w-full">
                  Send Reset Email
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Instructions */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Instructions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
          <p>1. Make sure the Django backend server is running on http://127.0.0.1:8000</p>
          <p>2. Start the backend with: <code className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">cd backend && python manage.py runserver</code></p>
          <p>3. Test registration by filling out the form and clicking Register</p>
          <p>4. Test login with the registered credentials</p>
          <p>5. Test the protected endpoint after successful login</p>
          <p>6. Test forgot password functionality</p>
        </CardContent>
      </Card>
    </div>
  );
}