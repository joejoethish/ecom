'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Badge } from '@/components/ui/Badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/Select';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import {
    Users, UserPlus, Mail, MoreHorizontal, Shield,
    CheckCircle, XCircle, Clock, AlertTriangle
} from 'lucide-react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface TenantUser {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    full_name: string;
    role: string;
    phone?: string;
    avatar?: string;
    department?: string;
    job_title?: string;
    is_active: boolean;
    last_login?: string;
    date_joined: string;
}

interface TenantInvitation {
    id: string;
    email: string;
    role: string;
    status: string;
    invited_by_name: string;
    created_at: string;
    expires_at: string;
    is_expired: boolean;
}

interface TenantUserManagementProps {
    tenantId: string;
}

export default function TenantUserManagement({ tenantId }: TenantUserManagementProps) {
    const [users, setUsers] = useState<TenantUser[]>([]);
    const [invitations, setInvitations] = useState<TenantInvitation[]>([]);
    const [loading, setLoading] = useState(true);
    const [showInviteDialog, setShowInviteDialog] = useState(false);
    const [inviteForm, setInviteForm] = useState({ email: '', role: 'staff' });
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    useEffect(() => {
        fetchUsers();
        fetchInvitations();
    }, [tenantId]);

    const fetchUsers = async () => {
        try {
            const response = await fetch('/api/tenants/users/');
            const data = await response.json();
            setUsers(data.results || data);
        } catch (error) {
            console.error('Error fetching users:', error);
        }
    };

    const fetchInvitations = async () => {
        try {
            const response = await fetch('/api/tenants/invitations/');
            const data = await response.json();
            setInvitations(data.results || data);
        } catch (error) {
            console.error('Error fetching invitations:', error);
        } finally {
            setLoading(false);
        }
    };

    const inviteUser = async () => {
        try {
            const response = await fetch('/api/tenants/users/invite/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(inviteForm),
            });

            if (response.ok) {
                setMessage({ type: 'success', text: 'Invitation sent successfully' });
                setShowInviteDialog(false);
                setInviteForm({ email: '', role: 'staff' });
                fetchInvitations();
            } else {
                const error = await response.json();
                throw new Error(error.message || 'Failed to send invitation');
            }
        } catch (error) {
            console.error('Error sending invitation:', error);
            setMessage({ type: 'error', text: error.message || 'Failed to send invitation' });
        }
    };

    const toggleUserStatus = async (userId: string, isActive: boolean) => {
        try {
            const action = isActive ? 'deactivate' : 'activate';
            const response = await fetch(`/api/tenants/users/${userId}/${action}/`, {
                method: 'POST',
            });

            if (response.ok) {
                setMessage({
                    type: 'success',
                    text: `User ${isActive ? 'deactivated' : 'activated'} successfully`
                });
                fetchUsers();
            } else {
                throw new Error('Failed to update user status');
            }
        } catch (error) {
            console.error('Error updating user status:', error);
            setMessage({ type: 'error', text: 'Failed to update user status' });
        }
    };

    const resendInvitation = async (invitationId: string) => {
        try {
            const response = await fetch(`/api/tenants/invitations/${invitationId}/resend/`, {
                method: 'POST',
            });

            if (response.ok) {
                setMessage({ type: 'success', text: 'Invitation resent successfully' });
                fetchInvitations();
            } else {
                throw new Error('Failed to resend invitation');
            }
        } catch (error) {
            console.error('Error resending invitation:', error);
            setMessage({ type: 'error', text: 'Failed to resend invitation' });
        }
    };

    const cancelInvitation = async (invitationId: string) => {
        try {
            const response = await fetch(`/api/tenants/invitations/${invitationId}/cancel/`, {
                method: 'POST',
            });

            if (response.ok) {
                setMessage({ type: 'success', text: 'Invitation cancelled successfully' });
                fetchInvitations();
            } else {
                throw new Error('Failed to cancel invitation');
            }
        } catch (error) {
            console.error('Error cancelling invitation:', error);
            setMessage({ type: 'error', text: 'Failed to cancel invitation' });
        }
    };

    const getRoleBadgeColor = (role: string) => {
        switch (role) {
            case 'owner': return 'bg-purple-100 text-purple-800';
            case 'admin': return 'bg-red-100 text-red-800';
            case 'manager': return 'bg-blue-100 text-blue-800';
            case 'staff': return 'bg-green-100 text-green-800';
            case 'viewer': return 'bg-gray-100 text-gray-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'pending': return <Clock className="h-4 w-4 text-yellow-500" />;
            case 'accepted': return <CheckCircle className="h-4 w-4 text-green-500" />;
            case 'expired': return <XCircle className="h-4 w-4 text-red-500" />;
            case 'cancelled': return <XCircle className="h-4 w-4 text-gray-500" />;
            default: return <Clock className="h-4 w-4 text-gray-500" />;
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Message */}
            {message && (
                <Alert className={
                    message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                }>
                    {message.type === 'success' ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                        <AlertTriangle className="h-4 w-4 text-red-600" />
                    )}
                    <AlertDescription>{message.text}</AlertDescription>
                </Alert>
            )}

            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold">User Management</h2>
                    <p className="text-muted-foreground">
                        Manage users and invitations for your tenant
                    </p>
                </div>
                <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
                    <DialogTrigger asChild>
                        <Button>
                            <UserPlus className="h-4 w-4 mr-2" />
                            Invite User
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Invite New User</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="email">Email Address</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    value={inviteForm.email}
                                    onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                                    placeholder="user@example.com"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="role">Role</Label>
                                <Select
                                    value={inviteForm.role}
                                    onValueChange={(value) => setInviteForm({ ...inviteForm, role: value })}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="viewer">Viewer</SelectItem>
                                        <SelectItem value="staff">Staff</SelectItem>
                                        <SelectItem value="manager">Manager</SelectItem>
                                        <SelectItem value="admin">Admin</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="flex justify-end space-x-2">
                                <Button variant="outline" onClick={() => setShowInviteDialog(false)}>
                                    Cancel
                                </Button>
                                <Button onClick={inviteUser}>
                                    <Mail className="h-4 w-4 mr-2" />
                                    Send Invitation
                                </Button>
                            </div>
                        </div>
                    </DialogContent>
                </Dialog>
            </div>

            {/* Users Table */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center">
                        <Users className="h-5 w-5 mr-2" />
                        Active Users ({users.length})
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>User</TableHead>
                                <TableHead>Role</TableHead>
                                <TableHead>Department</TableHead>
                                <TableHead>Last Login</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {users.map((user) => (
                                <TableRow key={user.id}>
                                    <TableCell>
                                        <div className="flex items-center space-x-3">
                                            <Avatar>
                                                <AvatarImage src={user.avatar} />
                                                <AvatarFallback>
                                                    {user.first_name?.[0]}{user.last_name?.[0]}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div>
                                                <div className="font-medium">{user.full_name || user.username}</div>
                                                <div className="text-sm text-muted-foreground">{user.email}</div>
                                            </div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Badge className={getRoleBadgeColor(user.role)}>
                                            {user.role}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>{user.department || '-'}</TableCell>
                                    <TableCell>
                                        {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant={user.is_active ? 'default' : 'secondary'}>
                                            {user.is_active ? 'Active' : 'Inactive'}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="sm">
                                                    <MoreHorizontal className="h-4 w-4" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent>
                                                <DropdownMenuItem>
                                                    <Shield className="h-4 w-4 mr-2" />
                                                    Edit Permissions
                                                </DropdownMenuItem>
                                                <DropdownMenuItem
                                                    onClick={() => toggleUserStatus(user.id, user.is_active)}
                                                >
                                                    {user.is_active ? (
                                                        <>
                                                            <XCircle className="h-4 w-4 mr-2" />
                                                            Deactivate
                                                        </>
                                                    ) : (
                                                        <>
                                                            <CheckCircle className="h-4 w-4 mr-2" />
                                                            Activate
                                                        </>
                                                    )}
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Pending Invitations */}
            {invitations.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center">
                            <Mail className="h-5 w-5 mr-2" />
                            Pending Invitations ({invitations.length})
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Email</TableHead>
                                    <TableHead>Role</TableHead>
                                    <TableHead>Invited By</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Expires</TableHead>
                                    <TableHead>Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {invitations.map((invitation) => (
                                    <TableRow key={invitation.id}>
                                        <TableCell>{invitation.email}</TableCell>
                                        <TableCell>
                                            <Badge className={getRoleBadgeColor(invitation.role)}>
                                                {invitation.role}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>{invitation.invited_by_name}</TableCell>
                                        <TableCell>
                                            <div className="flex items-center space-x-2">
                                                {getStatusIcon(invitation.status)}
                                                <span className="capitalize">{invitation.status}</span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            {new Date(invitation.expires_at).toLocaleDateString()}
                                        </TableCell>
                                        <TableCell>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="sm">
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent>
                                                    {invitation.status === 'pending' && !invitation.is_expired && (
                                                        <DropdownMenuItem
                                                            onClick={() => resendInvitation(invitation.id)}
                                                        >
                                                            <Mail className="h-4 w-4 mr-2" />
                                                            Resend
                                                        </DropdownMenuItem>
                                                    )}
                                                    {invitation.status === 'pending' && (
                                                        <DropdownMenuItem
                                                            onClick={() => cancelInvitation(invitation.id)}
                                                        >
                                                            <XCircle className="h-4 w-4 mr-2" />
                                                            Cancel
                                                        </DropdownMenuItem>
                                                    )}
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}