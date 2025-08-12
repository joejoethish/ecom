import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/Badge';
import { 
  X, 
  Search, 
  ExternalLink, 
  ArrowRight,
  Settings,
  Key,
  Globe,
  Shield
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
  supported_features: string[];
  is_popular: boolean;
}

interface IntegrationCategory {
  id: string;
  name: string;
  category: string;
  description: string;
}

interface CreateIntegrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  providers: IntegrationProvider[];
  categories: IntegrationCategory[];
  onCreate: (data: any) => Promise<any>;
}

export default function CreateIntegrationModal({
  isOpen,
  onClose,
  providers,
  categories,
  onCreate
}: CreateIntegrationModalProps) {
  const [step, setStep] = useState<'select' | 'configure'>('select');
  const [selectedProvider, setSelectedProvider] = useState<IntegrationProvider | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(false);
  
  // Configuration form state
  const [formData, setFormData] = useState({
    name: '',
    environment: 'production',
    configuration: {} as Record<string, string>
  });

  if (!isOpen) return null;

  const filteredProviders = providers.filter(provider => {
    const matchesSearch = provider.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         provider.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || provider.category_name === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleProviderSelect = (provider: IntegrationProvider) => {
    setSelectedProvider(provider);
    setFormData(prev => ({
      ...prev,
      name: `${provider.name} Integration`
    }));
    setStep('configure');
  };

  const handleConfigurationChange = (key: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      configuration: {
        ...prev.configuration,
        [key]: value
      }
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProvider) return;

    setLoading(true);
    try {
      await onCreate({
        name: formData.name,
        provider: selectedProvider.id,
        environment: formData.environment,
        configuration: formData.configuration
      });
      
      // Reset form and close modal
      setStep('select');
      setSelectedProvider(null);
      setFormData({ name: '', environment: 'production', configuration: {} });
      onClose();
    } catch (error) {
      console.error('Failed to create integration:', error);
    } finally {
      setLoading(false);
    }
  };

  const getConfigurationFields = (provider: IntegrationProvider) => {
    // Define configuration fields based on provider type
    const commonFields = [
      { key: 'api_key', label: 'API Key', type: 'password', required: true },
      { key: 'api_secret', label: 'API Secret', type: 'password', required: false }
    ];

    switch (provider.slug) {
      case 'stripe':
        return [
          { key: 'publishable_key', label: 'Publishable Key', type: 'text', required: true },
          { key: 'secret_key', label: 'Secret Key', type: 'password', required: true },
          { key: 'webhook_secret', label: 'Webhook Secret', type: 'password', required: false }
        ];
      case 'paypal':
        return [
          { key: 'client_id', label: 'Client ID', type: 'text', required: true },
          { key: 'client_secret', label: 'Client Secret', type: 'password', required: true }
        ];
      case 'mailchimp':
        return [
          { key: 'api_key', label: 'API Key', type: 'password', required: true },
          { key: 'server_prefix', label: 'Server Prefix', type: 'text', required: true }
        ];
      default:
        return commonFields;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {step === 'select' ? 'Add Integration' : 'Configure Integration'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {step === 'select' 
                ? 'Choose a provider to integrate with your system'
                : `Configure your ${selectedProvider?.name} integration`
              }
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {step === 'select' ? (
            <div className="space-y-6">
              {/* Search and Filter */}
              <div className="flex flex-wrap gap-4">
                <div className="flex-1 min-w-[300px]">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                      placeholder="Search providers..."
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
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Provider Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredProviders.map((provider) => (
                  <Card
                    key={provider.id}
                    className="cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => handleProviderSelect(provider)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center space-x-3 mb-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                          {provider.logo_url ? (
                            <img
                              src={provider.logo_url}
                              alt={provider.name}
                              className="w-6 h-6 object-contain"
                            />
                          ) : (
                            <Settings className="h-5 w-5 text-gray-400" />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h3 className="font-medium text-gray-900">{provider.name}</h3>
                            {provider.is_popular && (
                              <Badge variant="secondary" className="text-xs">Popular</Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-500">{provider.category_name}</p>
                        </div>
                        <ArrowRight className="h-4 w-4 text-gray-400" />
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {provider.description}
                      </p>
                      
                      {provider.supported_features.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {provider.supported_features.slice(0, 3).map((feature, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {feature}
                            </Badge>
                          ))}
                          {provider.supported_features.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{provider.supported_features.length - 3}
                            </Badge>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>

              {filteredProviders.length === 0 && (
                <div className="text-center py-12">
                  <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                    <Search className="h-8 w-8 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No providers found</h3>
                  <p className="text-gray-500">
                    Try adjusting your search terms or category filter.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Provider Info */}
              {selectedProvider && (
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                        {selectedProvider.logo_url ? (
                          <img
                            src={selectedProvider.logo_url}
                            alt={selectedProvider.name}
                            className="w-8 h-8 object-contain"
                          />
                        ) : (
                          <Settings className="h-6 w-6 text-gray-400" />
                        )}
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{selectedProvider.name}</h3>
                        <p className="text-sm text-gray-500">{selectedProvider.category_name}</p>
                      </div>
                      <div className="flex space-x-2">
                        <a
                          href={selectedProvider.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                        {selectedProvider.documentation_url && (
                          <a
                            href={selectedProvider.documentation_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800"
                          >
                            <Globe className="h-4 w-4" />
                          </a>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Basic Configuration */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">Basic Configuration</h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Integration Name
                  </label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter integration name"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Environment
                  </label>
                  <select
                    value={formData.environment}
                    onChange={(e) => setFormData(prev => ({ ...prev, environment: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="production">Production</option>
                    <option value="sandbox">Sandbox</option>
                    <option value="development">Development</option>
                  </select>
                </div>
              </div>

              {/* Provider-specific Configuration */}
              {selectedProvider && (
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Key className="h-5 w-5 text-gray-400" />
                    <h3 className="text-lg font-medium text-gray-900">API Configuration</h3>
                  </div>
                  
                  {getConfigurationFields(selectedProvider).map((field) => (
                    <div key={field.key}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {field.label}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                      </label>
                      <Input
                        type={field.type}
                        value={formData.configuration[field.key] || ''}
                        onChange={(e) => handleConfigurationChange(field.key, e.target.value)}
                        placeholder={`Enter ${field.label.toLowerCase()}`}
                        required={field.required}
                      />
                    </div>
                  ))}
                </div>
              )}

              {/* Security Notice */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-medium text-blue-900">Security Notice</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      Your API credentials will be encrypted and stored securely. 
                      We recommend using environment-specific credentials and enabling 
                      webhook signature verification when available.
                    </p>
                  </div>
                </div>
              </div>
            </form>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <div>
            {step === 'configure' && (
              <Button
                variant="outline"
                onClick={() => setStep('select')}
                disabled={loading}
              >
                Back
              </Button>
            )}
          </div>
          
          <div className="flex space-x-3">
            <Button variant="outline" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            
            {step === 'configure' && (
              <Button
                onClick={handleSubmit}
                disabled={loading || !formData.name || !selectedProvider}
              >
                {loading ? 'Creating...' : 'Create Integration'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}