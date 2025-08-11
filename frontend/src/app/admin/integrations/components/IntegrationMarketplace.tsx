import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
    Search,
    Star,
    ExternalLink,
    Plus,
    Filter,
    Grid,
    List,
    TrendingUp
} from 'lucide-react';

interface IntegrationProvider {
    id: string;
    name: string;
    slug: string;
    category_name: string;
    description: string;
    website_url: string;
    documentation_url: string;
    logo_url: string;
    status: string;
    supported_features: string[];
    is_popular: boolean;
    integration_count: number;
}

interface IntegrationCategory {
    id: string;
    name: string;
    category: string;
    description: string;
    icon: string;
    integration_count: number;
}

interface IntegrationMarketplaceProps {
    providers: IntegrationProvider[];
    categories: IntegrationCategory[];
    onCreateIntegration: (provider: IntegrationProvider) => void;
}

export default function IntegrationMarketplace({
    providers,
    categories,
    onCreateIntegration
}: IntegrationMarketplaceProps) {
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [showPopularOnly, setShowPopularOnly] = useState(false);

    const filteredProviders = providers.filter(provider => {
        const matchesSearch = provider.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            provider.description.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesCategory = selectedCategory === 'all' || provider.category_name === selectedCategory;
        const matchesPopular = !showPopularOnly || provider.is_popular;

        return matchesSearch && matchesCategory && matchesPopular;
    });

    const popularProviders = providers.filter(provider => provider.is_popular).slice(0, 6);

    return (
        <div className="space-y-6">
            {/* Search and Filters */}
            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-wrap gap-4 items-center">
                        <div className="flex-1 min-w-[300px]">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                                <Input
                                    placeholder="Search integrations..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="pl-10"
                                />
                            </div>
                        </div>

                        <select
                            value={selectedCategory}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="all">All Categories</option>
                            {categories.map(category => (
                                <option key={category.id} value={category.name}>
                                    {category.name} ({category.integration_count})
                                </option>
                            ))}
                        </select>

                        <div className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                id="popular-only"
                                checked={showPopularOnly}
                                onChange={(e) => setShowPopularOnly(e.target.checked)}
                                className="rounded border-gray-300"
                            />
                            <label htmlFor="popular-only" className="text-sm font-medium">
                                Popular only
                            </label>
                        </div>

                        <div className="flex items-center space-x-1 border border-gray-300 rounded-md">
                            <Button
                                variant={viewMode === 'grid' ? 'default' : 'ghost'}
                                size="sm"
                                onClick={() => setViewMode('grid')}
                                className="rounded-r-none"
                            >
                                <Grid className="h-4 w-4" />
                            </Button>
                            <Button
                                variant={viewMode === 'list' ? 'default' : 'ghost'}
                                size="sm"
                                onClick={() => setViewMode('list')}
                                className="rounded-l-none"
                            >
                                <List className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Popular Integrations */}
            {!searchTerm && selectedCategory === 'all' && !showPopularOnly && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center">
                            <TrendingUp className="h-5 w-5 mr-2" />
                            Popular Integrations
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {popularProviders.map((provider) => (
                                <div
                                    key={provider.id}
                                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                                >
                                    <div className="flex items-center space-x-3 mb-3">
                                        <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                                            {provider.logo_url ? (
                                                <img
                                                    src={provider.logo_url}
                                                    alt={provider.name}
                                                    className="w-6 h-6 object-contain"
                                                />
                                            ) : (
                                                <div className="w-6 h-6 bg-gray-300 rounded"></div>
                                            )}
                                        </div>
                                        <div className="flex-1">
                                            <h3 className="font-medium text-gray-900">{provider.name}</h3>
                                            <p className="text-sm text-gray-500">{provider.category_name}</p>
                                        </div>
                                        <Badge variant="secondary" className="text-xs">
                                            <Star className="h-3 w-3 mr-1" />
                                            Popular
                                        </Badge>
                                    </div>
                                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                                        {provider.description}
                                    </p>
                                    <Button
                                        size="sm"
                                        className="w-full"
                                        onClick={() => onCreateIntegration(provider)}
                                    >
                                        <Plus className="h-4 w-4 mr-2" />
                                        Add Integration
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* All Integrations */}
            <Card>
                <CardHeader>
                    <CardTitle>
                        All Integrations ({filteredProviders.length})
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {viewMode === 'grid' ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {filteredProviders.map((provider) => (
                                <div
                                    key={provider.id}
                                    className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
                                >
                                    <div className="flex items-center space-x-3 mb-4">
                                        <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                                            {provider.logo_url ? (
                                                <img
                                                    src={provider.logo_url}
                                                    alt={provider.name}
                                                    className="w-8 h-8 object-contain"
                                                />
                                            ) : (
                                                <div className="w-8 h-8 bg-gray-300 rounded"></div>
                                            )}
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex items-center space-x-2">
                                                <h3 className="font-semibold text-gray-900">{provider.name}</h3>
                                                {provider.is_popular && (
                                                    <Badge variant="secondary" className="text-xs">
                                                        <Star className="h-3 w-3 mr-1" />
                                                        Popular
                                                    </Badge>
                                                )}
                                            </div>
                                            <p className="text-sm text-gray-500">{provider.category_name}</p>
                                        </div>
                                    </div>

                                    <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                                        {provider.description}
                                    </p>

                                    {provider.supported_features.length > 0 && (
                                        <div className="mb-4">
                                            <p className="text-xs font-medium text-gray-700 mb-2">Features:</p>
                                            <div className="flex flex-wrap gap-1">
                                                {provider.supported_features.slice(0, 3).map((feature, index) => (
                                                    <Badge key={index} variant="outline" className="text-xs">
                                                        {feature}
                                                    </Badge>
                                                ))}
                                                {provider.supported_features.length > 3 && (
                                                    <Badge variant="outline" className="text-xs">
                                                        +{provider.supported_features.length - 3} more
                                                    </Badge>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                                            <span>{provider.integration_count} active</span>
                                            <a
                                                href={provider.website_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="flex items-center hover:text-blue-600"
                                            >
                                                <ExternalLink className="h-3 w-3 mr-1" />
                                                Website
                                            </a>
                                        </div>
                                    </div>

                                    <Button
                                        className="w-full"
                                        onClick={() => onCreateIntegration(provider)}
                                    >
                                        <Plus className="h-4 w-4 mr-2" />
                                        Add Integration
                                    </Button>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {filteredProviders.map((provider) => (
                                <div
                                    key={provider.id}
                                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                                >
                                    <div className="flex items-center space-x-4">
                                        <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                                            {provider.logo_url ? (
                                                <img
                                                    src={provider.logo_url}
                                                    alt={provider.name}
                                                    className="w-8 h-8 object-contain"
                                                />
                                            ) : (
                                                <div className="w-8 h-8 bg-gray-300 rounded"></div>
                                            )}
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center space-x-2 mb-1">
                                                <h3 className="font-semibold text-gray-900">{provider.name}</h3>
                                                {provider.is_popular && (
                                                    <Badge variant="secondary" className="text-xs">
                                                        <Star className="h-3 w-3 mr-1" />
                                                        Popular
                                                    </Badge>
                                                )}
                                            </div>
                                            <p className="text-sm text-gray-500 mb-2">{provider.category_name}</p>
                                            <p className="text-sm text-gray-600 line-clamp-2">
                                                {provider.description}
                                            </p>
                                        </div>

                                        <div className="flex flex-col items-end space-y-2">
                                            <div className="flex items-center space-x-2 text-xs text-gray-500">
                                                <span>{provider.integration_count} active</span>
                                                <a
                                                    href={provider.website_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="flex items-center hover:text-blue-600"
                                                >
                                                    <ExternalLink className="h-3 w-3 mr-1" />
                                                    Website
                                                </a>
                                            </div>
                                            <Button
                                                size="sm"
                                                onClick={() => onCreateIntegration(provider)}
                                            >
                                                <Plus className="h-4 w-4 mr-2" />
                                                Add Integration
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {filteredProviders.length === 0 && (
                        <div className="text-center py-12">
                            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                                <Search className="h-8 w-8 text-gray-400" />
                            </div>
                            <h3 className="text-lg font-medium text-gray-900 mb-2">No integrations found</h3>
                            <p className="text-gray-500">
                                Try adjusting your search terms or filters.
                            </p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}