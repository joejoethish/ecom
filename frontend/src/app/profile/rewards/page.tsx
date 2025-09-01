'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { toast } from 'react-hot-toast';
import { 
  Trophy, 
  Star, 
  Gift, 
  TrendingUp, 
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Crown,
  Award
} from 'lucide-react';
import { apiClient } from '@/utils/api';
import { API_ENDPOINTS } from '@/constants';
import { formatCurrency } from '@/utils/currency';

interface RewardTransaction {
  id: string;
  transaction_type: string;
  points: number;
  description: string;
  reference_id?: string;
  expires_at?: string;
  created_at: string;
}

interface CustomerRewards {
  id: string;
  total_points_earned: number;
  total_points_redeemed: number;
  current_points: number;
  tier: 'bronze' | 'silver' | 'gold' | 'platinum';
  tier_benefits: string[];
  recent_transactions: RewardTransaction[];
  created_at: string;
  updated_at: string;
}

interface RewardProgram {
  id: string;
  name: string;
  description: string;
  points_per_dollar: number;
  dollar_per_point: number;
  minimum_redemption_points: number;
  maximum_redemption_points?: number;
  is_active: boolean;
}

export default function RewardsPage() {
  const [rewards, setRewards] = useState<CustomerRewards | null>(null);
  const [program, setProgram] = useState<RewardProgram | null>(null);
  const [transactions, setTransactions] = useState<RewardTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchRewardsData();
    fetchProgramData();
  }, []);

  const fetchRewardsData = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(API_ENDPOINTS.REWARDS.LIST);
      if (response.success && response.data) {
        setRewards(response.data);
      }
    } catch (error: any) {
      setError(error.message || 'Failed to load rewards data');
      toast.error('Failed to load rewards data');
    } finally {
      setLoading(false);
    }
  };

  const fetchProgramData = async () => {
    try {
      const response = await apiClient.get(`${API_ENDPOINTS.REWARDS.LIST}/program/`);
      if (response.success && response.data) {
        setProgram(response.data);
      }
    } catch (error: any) {
      console.error('Failed to load program data:', error);
    }
  };

  const fetchTransactions = async () => {
    try {
      setTransactionsLoading(true);
      const response = await apiClient.get(`${API_ENDPOINTS.REWARDS.LIST}/transactions/`);
      if (response.success && response.data) {
        setTransactions(response.data.results || []);
      }
    } catch (error: any) {
      toast.error('Failed to load transaction history');
    } finally {
      setTransactionsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'history') {
      fetchTransactions();
    }
  }, [activeTab]);

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'bronze': return 'bg-amber-100 text-amber-800';
      case 'silver': return 'bg-gray-100 text-gray-800';
      case 'gold': return 'bg-yellow-100 text-yellow-800';
      case 'platinum': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'bronze': return <Award className="h-4 w-4" />;
      case 'silver': return <Star className="h-4 w-4" />;
      case 'gold': return <Trophy className="h-4 w-4" />;
      case 'platinum': return <Crown className="h-4 w-4" />;
      default: return <Award className="h-4 w-4" />;
    }
  };

  const getTransactionIcon = (type: string, points: number) => {
    if (points > 0) {
      return <ArrowUpRight className="h-4 w-4 text-green-600" />;
    } else {
      return <ArrowDownRight className="h-4 w-4 text-red-600" />;
    }
  };

  const formatTransactionType = (type: string) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {Array.from({ length: 3 }).map((_, index) => (
            <Card key={index}>
              <CardContent className="p-6">
                <Skeleton className="h-12 w-12 mb-4" />
                <Skeleton className="h-6 w-24 mb-2" />
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error || !rewards) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="max-w-md mx-auto">
          <CardContent className="p-6 text-center">
            <Gift className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Error Loading Rewards
            </h3>
            <p className="text-gray-600 mb-4">{error || 'Failed to load rewards data'}</p>
            <Button onClick={fetchRewardsData}>
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">My Rewards</h1>
        <p className="text-gray-600">Earn points with every purchase and unlock exclusive benefits</p>
      </div>

      {/* Rewards Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Current Points</p>
                <p className="text-2xl font-bold text-gray-900">{rewards.current_points.toLocaleString()}</p>
              </div>
              <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Star className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            {program && (
              <p className="text-xs text-gray-500 mt-2">
                ≈ {formatCurrency(rewards.current_points * program.dollar_per_point)} value
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Member Tier</p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge className={getTierColor(rewards.tier)}>
                    {getTierIcon(rewards.tier)}
                    <span className="ml-1 capitalize">{rewards.tier}</span>
                  </Badge>
                </div>
              </div>
              <div className="h-12 w-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Trophy className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Lifetime Earned</p>
                <p className="text-2xl font-bold text-gray-900">{rewards.total_points_earned.toLocaleString()}</p>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {rewards.total_points_redeemed.toLocaleString()} points redeemed
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="benefits">Benefits</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {program && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Gift className="h-5 w-5" />
                  {program.name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">{program.description}</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-gray-600">Earn Rate</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {program.points_per_dollar} points per ${1}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-gray-600">Point Value</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatCurrency(program.dollar_per_point)} per point
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {rewards.recent_transactions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {rewards.recent_transactions.slice(0, 5).map((transaction) => (
                    <div key={transaction.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                      <div className="flex items-center gap-3">
                        {getTransactionIcon(transaction.transaction_type, transaction.points)}
                        <div>
                          <p className="font-medium text-gray-900">
                            {formatTransactionType(transaction.transaction_type)}
                          </p>
                          <p className="text-sm text-gray-600">{transaction.description}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`font-semibold ${transaction.points > 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {transaction.points > 0 ? '+' : ''}{transaction.points}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(transaction.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="benefits" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Crown className="h-5 w-5" />
                Your {rewards.tier.charAt(0).toUpperCase() + rewards.tier.slice(1)} Benefits
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {rewards.tier_benefits.map((benefit, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                    <p className="text-gray-700">{benefit}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Transaction History
              </CardTitle>
            </CardHeader>
            <CardContent>
              {transactionsLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 5 }).map((_, index) => (
                    <div key={index} className="flex items-center justify-between py-3">
                      <div className="flex items-center gap-3">
                        <Skeleton className="h-8 w-8 rounded" />
                        <div>
                          <Skeleton className="h-4 w-32 mb-1" />
                          <Skeleton className="h-3 w-48" />
                        </div>
                      </div>
                      <div className="text-right">
                        <Skeleton className="h-4 w-16 mb-1" />
                        <Skeleton className="h-3 w-20" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : transactions.length > 0 ? (
                <div className="space-y-3">
                  {transactions.map((transaction) => (
                    <div key={transaction.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
                      <div className="flex items-center gap-3">
                        {getTransactionIcon(transaction.transaction_type, transaction.points)}
                        <div>
                          <p className="font-medium text-gray-900">
                            {formatTransactionType(transaction.transaction_type)}
                          </p>
                          <p className="text-sm text-gray-600">{transaction.description}</p>
                          {transaction.reference_id && (
                            <p className="text-xs text-gray-500">Ref: {transaction.reference_id}</p>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`font-semibold ${transaction.points > 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {transaction.points > 0 ? '+' : ''}{transaction.points}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(transaction.created_at).toLocaleDateString()}
                        </p>
                        {transaction.expires_at && (
                          <p className="text-xs text-orange-500">
                            Expires: {new Date(transaction.expires_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No transaction history yet</p>
                  <p className="text-sm text-gray-500">Start shopping to earn your first points!</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}