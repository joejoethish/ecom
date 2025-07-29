'use client';

import { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Product } from '@/types';
import { formatCurrency } from '@/utils/format';
import { useAppDispatch } from '@/store';
import { addToCart } from '@/store/slices/cartSlice';
import { ROUTES } from '@/constants';

interface ProductDetailsProps {
  product: Product;
}

export function ProductDetails({ product }: ProductDetailsProps) {
  const dispatch = useAppDispatch();
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(
    product.images.find(img => img.is_primary)?.id || product.images[0]?.id
  );

  const {
    id,
    name,
    description,
    price,
    discount_price,
    category,
    brand,
    sku,
    images,
    status,
  } = product;

  const hasDiscount = discount_price !== undefined && discount_price < price;
  const effectivePrice = hasDiscount ? discount_price! : price;
  const discountPercentage = hasDiscount 
    ? Math.round(((price - discount_price!) / price) * 100) 
    : 0;
  
  const currentImage = images.find(img => img.id === selectedImage) || images[0];
  const isOutOfStock = status === 'out_of_stock';

  const handleQuantityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value);
    if (!isNaN(value) && value > 0) {
      setQuantity(value);
    }
  };

  const handleAddToCart = () => {
    if (!isOutOfStock) {
      dispatch(addToCart({ productId: id, quantity }));
    }
  };

  return (
    <div className="bg-white">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Product Images */}
        <div>
          <div className="relative aspect-square overflow-hidden rounded-lg mb-4 border">
            <Image
              src={currentImage?.image || '/placeholder-product.png'}
              alt={name}
              fill
              sizes="(max-width: 768px) 100vw, 50vw"
              className="object-contain"
            />
            {hasDiscount && (
              <div className="absolute top-4 left-4 bg-red-500 text-white px-3 py-1 rounded-md font-medium">
                {discountPercentage}% OFF
              </div>
            )}
          </div>
          
          {/* Thumbnail Gallery */}
          {images.length > 1 && (
            <div className="grid grid-cols-5 gap-2">
              {images.map(image => (
                <button
                  key={image.id}
                  onClick={() => setSelectedImage(image.id)}
                  className={`relative aspect-square rounded-md overflow-hidden border-2 ${
                    selectedImage === image.id ? 'border-blue-500' : 'border-gray-200'
                  }`}
                >
                  <Image
                    src={image.image}
                    alt={image.alt_text || name}
                    fill
                    sizes="20vw"
                    className="object-cover"
                  />
                </button>
              ))}
            </div>
          )}
        </div>
        
        {/* Product Info */}
        <div>
          {/* Breadcrumbs */}
          <nav className="mb-4">
            <ol className="flex text-sm">
              <li className="text-gray-500">
                <Link href={ROUTES.PRODUCTS} className="hover:text-gray-700">
                  Products
                </Link>
              </li>
              <li className="mx-2 text-gray-500">/</li>
              <li className="text-gray-500">
                <Link 
                  href={category?.slug ? `${ROUTES.PRODUCTS}?category=${category.slug}` : ROUTES.PRODUCTS} 
                  className="hover:text-gray-700"
                >
                  {category.name}
                </Link>
              </li>
              <li className="mx-2 text-gray-500">/</li>
              <li className="text-gray-900 font-medium truncate">{name}</li>
            </ol>
          </nav>
          
          {/* Product Title and Brand */}
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{name}</h1>
          {brand && <p className="text-gray-600 mb-4">Brand: {brand}</p>}
          
          {/* Price */}
          <div className="flex items-center mb-6">
            <span className="text-3xl font-bold text-gray-900">
              {formatCurrency(effectivePrice)}
            </span>
            {hasDiscount && (
              <span className="ml-3 text-lg text-gray-500 line-through">
                {formatCurrency(price)}
              </span>
            )}
          </div>
          
          {/* Status */}
          <div className="mb-6">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              isOutOfStock 
                ? 'bg-red-100 text-red-800' 
                : 'bg-green-100 text-green-800'
            }`}>
              {isOutOfStock ? 'Out of Stock' : 'In Stock'}
            </span>
          </div>
          
          {/* Description */}
          <div className="prose prose-sm max-w-none mb-6">
            <p>{description}</p>
          </div>
          
          {/* SKU */}
          <p className="text-sm text-gray-500 mb-6">SKU: {sku}</p>
          
          {/* Add to Cart */}
          <div className="flex items-center space-x-4 mb-8">
            <div className="w-24">
              <label htmlFor="quantity" className="sr-only">Quantity</label>
              <input
                type="number"
                id="quantity"
                name="quantity"
                min="1"
                value={quantity}
                onChange={handleQuantityChange}
                className="w-full border border-gray-300 rounded-md py-2 px-3 text-center focus:outline-none focus:ring-1 focus:ring-blue-500"
                disabled={isOutOfStock}
              />
            </div>
            <button
              onClick={handleAddToCart}
              disabled={isOutOfStock}
              className={`flex-1 py-3 px-6 rounded-md text-white font-medium ${
                isOutOfStock 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isOutOfStock ? 'Out of Stock' : 'Add to Cart'}
            </button>
          </div>
          
          {/* Additional Info */}
          <div className="border-t border-gray-200 pt-6">
            <dl className="grid grid-cols-1 gap-y-4 sm:grid-cols-2 sm:gap-x-6">
              <div>
                <dt className="text-sm font-medium text-gray-500">Category</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  <Link 
                    href={category?.slug ? `${ROUTES.PRODUCTS}?category=${category.slug}` : ROUTES.PRODUCTS}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    {category.name}
                  </Link>
                </dd>
              </div>
              {product.weight && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">Weight</dt>
                  <dd className="mt-1 text-sm text-gray-900">{product.weight} kg</dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}