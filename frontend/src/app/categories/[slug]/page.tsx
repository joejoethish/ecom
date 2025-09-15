import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { CategoryPage } from '@/components/categories/CategoryPage';
import { categoriesApi } from '@/services/categoriesApi';
import { productsApi } from '@/services/productsApi';

interface CategoryPageProps {
  params: {
    slug: string;
  };
  searchParams: {
    page?: string;
    sort?: string;
    brand?: string;
    price_min?: string;
    price_max?: string;
  };
}

export default async function Category({ params, searchParams }: CategoryPageProps) {
  const { slug } = params;
  const page = parseInt(searchParams.page || '1');
  const sort = searchParams.sort || 'name';
  
  try {
    // Fetch category details
    const categoryResponse = await categoriesApi.getCategoryDetails(slug);
    
    if (!categoryResponse.success || !categoryResponse.data) {
      notFound();
    }
    
    const category = categoryResponse.data;
    
    // Fetch products for this category
    const productsResponse = await productsApi.getProductsByCategory(slug, {
      page,
      sort,
      brand: searchParams.brand,
      price_min: searchParams.price_min ? parseFloat(searchParams.price_min) : undefined,
      price_max: searchParams.price_max ? parseFloat(searchParams.price_max) : undefined,
    });
    
    if (!productsResponse.success) {
      throw new Error('Failed to fetch products');
    }
    
    // Fetch category filters
    const filtersResponse = await categoriesApi.getCategoryFilters(slug);
    const filters = filtersResponse.success ? filtersResponse.data : null;
    
    return (
      <CategoryPage
        category={category}
        products={productsResponse.data}
        filters={filters}
        currentPage={page}
        searchParams={searchParams}
      />
    );
  } catch (error) {
    console.error('Error loading category page:', error);
    notFound();
  }
}

// Generate static params for known categories
export async function generateStaticParams() {
  try {
    const response = await categoriesApi.getAllCategories();
    
    if (response.success && response.data) {
      return response.data.data.map((category) => ({
        slug: category.slug,
      }));
    }
    
    return [];
  } catch (error) {
    console.error('Error generating static params for categories:', error);
    return [];
  }
}

// Generate metadata for SEO
export async function generateMetadata({ params }: CategoryPageProps): Promise<Metadata> {
  const { slug } = params;
  
  try {
    const response = await categoriesApi.getCategoryDetails(slug);
    
    if (response.success && response.data) {
      const category = response.data;
      
      return {
        title: `${category.name} - FlipMart`,
        description: category.description || `Shop ${category.name} products at FlipMart. Find the best deals and latest products.`,
        keywords: `${category.name}, products, shopping, ecommerce, FlipMart`,
        openGraph: {
          title: `${category.name} - FlipMart`,
          description: category.description || `Shop ${category.name} products at FlipMart`,
          type: 'website',
        },
      };
    }
  } catch (error) {
    console.error('Error generating metadata for category:', error);
  }
  
  return {
    title: 'Category - FlipMart',
    description: 'Shop products by category at FlipMart',
  };
}