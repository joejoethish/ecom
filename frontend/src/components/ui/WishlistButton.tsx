'use client';

import { useWishlist } from '@/hooks/useWishlist';
import Button from './Button';

interface WishlistButtonProps {
  productId: string;
  productName?: string;
  variant?: 'icon' | 'button';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function WishlistButton({ 
  productId, 
  productName, 
  variant = 'icon',
  size = 'md',
  className = '' 
}: WishlistButtonProps) {
  const { isInWishlist, toggleWishlist, loading } = useWishlist();
  const inWishlist = isInWishlist(productId);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    toggleWishlist(productId, productName);
  };

  if (variant === 'icon') {
    return (
      <button
        onClick={handleClick}
        disabled={loading}
        className={`p-2 rounded-full transition-colors ${
          inWishlist 
            ? 'text-red-500 hover:text-red-600 bg-red-50 hover:bg-red-100' 
            : 'text-gray-400 hover:text-red-500 bg-white hover:bg-red-50'
        } ${className}`}
        title={inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}
      >
        <svg 
          className={`w-5 h-5 ${size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-6 h-6' : 'w-5 h-5'}`}
          fill={inWishlist ? 'currentColor' : 'none'} 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" 
          />
        </svg>
      </button>
    );
  }

  return (
    <Button
      variant={inWishlist ? 'outline' : 'primary'}
      size={size}
      onClick={handleClick}
      loading={loading}
      className={`${inWishlist ? 'text-red-600 border-red-600 hover:bg-red-50' : ''} ${className}`}
    >
      <svg 
        className={`w-4 h-4 mr-2 ${size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-5 h-5' : 'w-4 h-4'}`}
        fill={inWishlist ? 'currentColor' : 'none'} 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" 
        />
      </svg>
      {inWishlist ? 'Remove from Wishlist' : 'Add to Wishlist'}
    </Button>
  );
}