import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Activity, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Zap,
  TrendingUp,
  TrendingDown
} from 'lucide-react';

interface IntegrationStatsProps {
  stats: {
    total_integrations: number;
    active_integrations: number;
    failed_integrations: number;
    total_syncs_today: number;
    successful_syncs_today: number;
    failed_syncs_today: number;
    total_api_calls_today: number;
    average_response_time: number;
    top_providers: Array<{ provider__name: string; count: number }>;
    recent_errors: Array<{
      integration: string;
      message: string;
      created_at: string;
    }>;
  } | null;
}

export default function IntegrationStats({ stats }: IntegrationStatsProps) {
  if (!stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-6">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const syncSuccessRate = stats.total_syncs_today > 0 
    ? (stats.successful_syncs_today / stats.total_syncs_today * 100).toFixed(1)
    : &apos;0&apos;;

  const statCards = [
    {
      title: &apos;Total Integrations&apos;,
      value: stats.total_integrations,
      icon: Activity,
      color: &apos;text-blue-600&apos;,
      bgColor: &apos;bg-blue-100&apos;,
      subtitle: `${stats.active_integrations} active`,
    },
    {
      title: &apos;Health Status&apos;,
      value: `${stats.active_integrations}/${stats.total_integrations}`,
      icon: stats.failed_integrations > 0 ? AlertCircle : CheckCircle,
      color: stats.failed_integrations > 0 ? &apos;text-red-600&apos; : &apos;text-green-600&apos;,
      bgColor: stats.failed_integrations > 0 ? &apos;bg-red-100&apos; : &apos;bg-green-100&apos;,
      subtitle: stats.failed_integrations > 0 ? `${stats.failed_integrations} failed` : &apos;All healthy&apos;,
    },
    {
      title: &apos;Syncs Today&apos;,
      value: stats.total_syncs_today,
      icon: Zap,
      color: &apos;text-purple-600&apos;,
      bgColor: &apos;bg-purple-100&apos;,
      subtitle: `${syncSuccessRate}% success rate`,
    },
    {
      title: &apos;API Calls&apos;,
      value: stats.total_api_calls_today,
      icon: TrendingUp,
      color: &apos;text-orange-600&apos;,
      bgColor: &apos;bg-orange-100&apos;,
      subtitle: `${stats.average_response_time}ms avg`,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <Card key={index}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                  <p className="text-sm text-gray-500 mt-1">{stat.subtitle}</p>
                </div>
                <div className={`p-3 rounded-full ${stat.bgColor}`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Providers */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Top Providers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.top_providers.slice(0, 5).map((provider, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm font-medium">{provider.provider__name}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ 
                          width: `${(provider.count / stats.total_integrations) * 100}%` 
                        }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600 w-8 text-right">
                      {provider.count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Errors */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Errors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.recent_errors.length > 0 ? (
                stats.recent_errors.slice(0, 5).map((error, index) => (
                  <div key={index} className="border-l-4 border-red-400 pl-3 py-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900">
                        {error.integration}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(error.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1 truncate">
                      {error.message}
                    </p>
                  </div>
                ))
              ) : (
                <div className="text-center py-4">
                  <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">No recent errors</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sync Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Today&apos;s Sync Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
              <p className="text-2xl font-bold text-green-600">
                {stats.successful_syncs_today}
              </p>
              <p className="text-sm text-gray-600">Successful Syncs</p>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <AlertCircle className="h-8 w-8 text-red-500" />
              </div>
              <p className="text-2xl font-bold text-red-600">
                {stats.failed_syncs_today}
              </p>
              <p className="text-sm text-gray-600">Failed Syncs</p>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Clock className="h-8 w-8 text-blue-500" />
              </div>
              <p className="text-2xl font-bold text-blue-600">
                {stats.average_response_time}ms
              </p>
              <p className="text-sm text-gray-600">Avg Response Time</p>
            </div>
          </div>
          
          {/* Success Rate Bar */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Success Rate</span>
              <span className="text-sm text-gray-600">{syncSuccessRate}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-green-500 h-3 rounded-full transition-all duration-300" 
                style={{ width: `${syncSuccessRate}%` }}
              ></div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}