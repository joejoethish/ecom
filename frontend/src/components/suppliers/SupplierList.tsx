import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import {
  Search, Download, Plus, Eye, Edit, Trash2,
  Building2, Phone, Mail, MapPin, TrendingUp, AlertTriangle,
  CheckCircle, Clock, Star
} from 'lucide-react';

interface Supplier {
  id: string;
  supplier_code: string;
  company_name: string;
  supplier_type: string;
  status: string;
  category_name: string;
  performance_score: number;
  quality_score: number;
  delivery_score: number;
  risk_level: string;
  total_orders: number;
  created_at: string;
  primary_contact_name: string;
  primary_contact_email: string;
  primary_contact_phone: string;
  address_line1: string;
  city: string;
  state: string;
  country: string;
}

interface SupplierFilters {
  search: string;
  status: string;
  supplier_type: string;
  risk_level: string;
  category: string;
}

const SupplierList: React.FC = () => {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<SupplierFilters>({
    search: '',
    status: '',
    supplier_type: '',
    risk_level: '',
    category: ''
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

  useEffect(() => {
    fetchSuppliers();
  }, [filters, currentPage]);

  const fetchSuppliers = async () => {
    setLoading(true);
    try {
      const queryParams = new URLSearchParams();
      
      if (filters.search) queryParams.append('search', filters.search);
      if (filters.status) queryParams.append('status', filters.status);
      if (filters.supplier_type) queryParams.append('supplier_type', filters.supplier_type);
      if (filters.risk_level) queryParams.append('risk_level', filters.risk_level);
      if (filters.category) queryParams.append('category', filters.category);
      queryParams.append('page', currentPage.toString());

      const response = await fetch(`/api/suppliers/suppliers/?${queryParams}`);
      const data = await response.json();
      
      setSuppliers(data.results || []);
      setTotalPages(Math.ceil(data.count / 20)); // Assuming 20 items per page
    } catch (error) {
      console.error('Error fetching suppliers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: keyof SupplierFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1); // Reset to first page when filtering
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: { variant: 'default' as const, label: 'Active' },
      inactive: { variant: 'secondary' as const, label: 'Inactive' },
      pending: { variant: 'outline' as const, label: 'Pending' },
      suspended: { variant: 'destructive' as const, label: 'Suspended' },
      blacklisted: { variant: 'destructive' as const, label: 'Blacklisted' }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || 
                  { variant: 'secondary' as const, label: status };
    
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getRiskBadge = (riskLevel: string) => {
    const riskConfig = {
      low: { variant: 'default' as const, label: 'Low Risk', icon: CheckCircle },
      medium: { variant: 'outline' as const, label: 'Medium Risk', icon: Clock },
      high: { variant: 'destructive' as const, label: 'High Risk', icon: AlertTriangle },
      critical: { variant: 'destructive' as const, label: 'Critical Risk', icon: AlertTriangle }
    };
    
    const config = riskConfig[riskLevel as keyof typeof riskConfig] || 
                  { variant: 'secondary' as const, label: riskLevel, icon: Clock };
    
    const IconComponent = config.icon;
    
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <IconComponent className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  const getPerformanceStars = (score: number) => {
    const fullStars = Math.floor(score);
    const hasHalfStar = score % 1 >= 0.5;
    
    return (
      <div className="flex items-center gap-1">
        {[...Array(5)].map((_, i) => (
          <Star
            key={i}
            className={`h-4 w-4 ${
              i < fullStars
                ? 'text-yellow-400 fill-current'
                : i === fullStars && hasHalfStar
                ? 'text-yellow-400 fill-current opacity-50'
                : 'text-gray-300'
            }`}
          />
        ))}
        <span className="text-sm text-gray-600 ml-1">({score.toFixed(1)})</span>
      </div>
    );
  };

  const exportSuppliers = async () => {
    try {
      const queryParams = new URLSearchParams();
      if (filters.search) queryParams.append('search', filters.search);
      if (filters.status) queryParams.append('status', filters.status);
      if (filters.supplier_type) queryParams.append('supplier_type', filters.supplier_type);
      if (filters.risk_level) queryParams.append('risk_level', filters.risk_level);

      const response = await fetch(`/api/suppliers/suppliers/export_csv/?${queryParams}`);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'suppliers.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error exporting suppliers:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Supplier Management</h1>
          <p className="text-gray-600">Manage and monitor your supplier relationships</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={exportSuppliers}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Supplier
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search suppliers..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select
              value={filters.status}
              onChange={(value) => handleFilterChange('status', value)}
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="pending">Pending</option>
              <option value="suspended">Suspended</option>
              <option value="blacklisted">Blacklisted</option>
            </Select>

            <Select
              value={filters.supplier_type}
              onChange={(value) => handleFilterChange('supplier_type', value)}
            >
              <option value="">All Types</option>
              <option value="manufacturer">Manufacturer</option>
              <option value="distributor">Distributor</option>
              <option value="wholesaler">Wholesaler</option>
              <option value="service_provider">Service Provider</option>
              <option value="dropshipper">Dropshipper</option>
            </Select>

            <Select
              value={filters.risk_level}
              onChange={(value) => handleFilterChange('risk_level', value)}
            >
              <option value="">All Risk Levels</option>
              <option value="low">Low Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="high">High Risk</option>
              <option value="critical">Critical Risk</option>
            </Select>

            <div className="flex space-x-2">
              <Button
                variant={viewMode === 'grid' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setViewMode('grid')}
              >
                Grid
              </Button>
              <Button
                variant={viewMode === 'table' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setViewMode('table')}
              >
                Table
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Supplier List */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {suppliers.map((supplier) => (
            <Card key={supplier.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{supplier.company_name}</CardTitle>
                    <p className="text-sm text-gray-600">{supplier.supplier_code}</p>
                  </div>
                  <div className="flex space-x-1">
                    <Button variant="ghost" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Edit className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  {getStatusBadge(supplier.status)}
                  {getRiskBadge(supplier.risk_level)}
                </div>

                <div className="space-y-2">
                  <div className="flex items-center text-sm text-gray-600">
                    <Building2 className="h-4 w-4 mr-2" />
                    {supplier.supplier_type.replace('_', ' ').toUpperCase()}
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-600">
                    <Phone className="h-4 w-4 mr-2" />
                    {supplier.primary_contact_phone}
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-600">
                    <Mail className="h-4 w-4 mr-2" />
                    {supplier.primary_contact_email}
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-600">
                    <MapPin className="h-4 w-4 mr-2" />
                    {supplier.city}, {supplier.state}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Performance</span>
                    {getPerformanceStars(supplier.performance_score)}
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Quality</span>
                    {getPerformanceStars(supplier.quality_score)}
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Delivery</span>
                    {getPerformanceStars(supplier.delivery_score)}
                  </div>
                </div>

                <div className="flex justify-between items-center pt-2 border-t">
                  <div className="text-center">
                    <div className="text-lg font-semibold">{supplier.total_orders}</div>
                    <div className="text-xs text-gray-600">Orders</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-green-600">
                      <TrendingUp className="h-4 w-4 inline mr-1" />
                      Active
                    </div>
                    <div className="text-xs text-gray-600">Status</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Supplier
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Risk Level
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Performance
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Orders
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {suppliers.map((supplier) => (
                    <tr key={supplier.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {supplier.company_name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {supplier.supplier_code}
                          </div>
                          <div className="text-sm text-gray-500">
                            {supplier.primary_contact_name}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {supplier.supplier_type.replace('_', ' ').toUpperCase()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(supplier.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getRiskBadge(supplier.risk_level)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="space-y-1">
                          <div className="flex items-center">
                            <span className="text-xs text-gray-600 w-16">Overall:</span>
                            {getPerformanceStars(supplier.performance_score)}
                          </div>
                          <div className="flex items-center">
                            <span className="text-xs text-gray-600 w-16">Quality:</span>
                            {getPerformanceStars(supplier.quality_score)}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {supplier.total_orders}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-800">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2">
          <Button
            variant="outline"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
          >
            Previous
          </Button>
          
          <div className="flex space-x-1">
            {[...Array(Math.min(5, totalPages))].map((_, i) => {
              const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
              return (
                <Button
                  key={pageNum}
                  variant={currentPage === pageNum ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => setCurrentPage(pageNum)}
                >
                  {pageNum}
                </Button>
              );
            })}
          </div>
          
          <Button
            variant="outline"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
          >
            Next
          </Button>
        </div>
      )}

      {/* Empty State */}
      {suppliers.length === 0 && !loading && (
        <Card>
          <CardContent className="text-center py-12">
            <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No suppliers found</h3>
            <p className="text-gray-600 mb-4">
              {Object.values(filters).some(f => f) 
                ? 'Try adjusting your filters to see more results.'
                : 'Get started by adding your first supplier.'
              }
            </p>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Supplier
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SupplierList;