# Customer Profile Components

This directory contains React components for managing customer profiles, addresses, preferences, and wishlists in the ecommerce platform.

## Components Overview

### CustomerProfileLayout
A layout component that provides navigation between different profile sections.

**Features:**
- Responsive sidebar navigation
- Mobile-friendly menu toggle
- Active state highlighting
- Consistent layout across profile pages

**Usage:**
```tsx
import { CustomerProfileLayout } from '@/components/customer';

<CustomerProfileLayout>
  <YourProfileContent />
</CustomerProfileLayout>
```

### CustomerProfile
Main customer profile information component for viewing and editing customer details.

**Features:**
- Display basic user information
- Edit customer-specific fields (date of birth, gender)
- Form validation
- Loading states
- Success/error notifications

**Redux Dependencies:**
- `customer/fetchProfile`
- `customer/updateProfile`

### CustomerPreferences
Component for managing customer notification and localization preferences.

**Features:**
- Toggle notification preferences (email, SMS, newsletter)
- Language and currency selection
- Real-time preference updates
- Form validation

**Redux Dependencies:**
- `customer/fetchProfile`
- `customer/updatePreferences`

### AddressManagement
Comprehensive address management component with CRUD operations.

**Features:**
- View all saved addresses
- Add new addresses
- Edit existing addresses
- Delete addresses
- Set default address
- Address type categorization (Home, Work, Other)
- Form validation with postal code and phone validation

**Redux Dependencies:**
- `customer/fetchAddresses`
- `customer/createAddress`
- `customer/updateAddress`
- `customer/deleteAddress`

### Wishlist
Wishlist management component for viewing and managing saved products.

**Features:**
- Display wishlist items with product details
- Remove items from wishlist
- Add items to cart
- Clear entire wishlist
- Empty state handling
- Product image display
- Price information with discount handling

**Redux Dependencies:**
- `wishlist/fetch`
- `wishlist/remove`
- `wishlist/clear`
- `cart/add` (for adding to cart)

## Supporting Components

### WishlistButton (UI Component)
Reusable button component for adding/removing items from wishlist.

**Props:**
- `productId`: Product ID to add/remove
- `productName`: Product name for notifications
- `variant`: 'icon' or 'button' display style
- `size`: 'sm', 'md', or 'lg'
- `className`: Additional CSS classes

**Usage:**
```tsx
import { WishlistButton } from '@/components/ui';

// Icon variant
<WishlistButton 
  productId="123" 
  productName="Product Name"
  variant="icon"
/>

// Button variant
<WishlistButton 
  productId="123" 
  productName="Product Name"
  variant="button"
  size="sm"
/>
```

## Hooks

### useWishlist
Custom hook for wishlist operations across components.

**Returns:**
- `wishlist`: Current wishlist state
- `loading`: Loading state
- `isInWishlist(productId)`: Check if product is in wishlist
- `toggleWishlist(productId, productName)`: Add/remove from wishlist
- `addToWishlist(productId, productName)`: Add to wishlist
- `removeFromWishlist(itemId, productName)`: Remove from wishlist
- `refreshWishlist()`: Refresh wishlist data

## Redux Slices

### customerSlice
Manages customer profile and address data.

**State:**
- `profile`: Customer profile information
- `addresses`: Array of customer addresses
- `loading`: Loading state
- `error`: Error messages

**Actions:**
- `fetchCustomerProfile`
- `updateCustomerProfile`
- `updateCustomerPreferences`
- `fetchCustomerAddresses`
- `createCustomerAddress`
- `updateCustomerAddress`
- `deleteCustomerAddress`

### wishlistSlice
Manages wishlist data and operations.

**State:**
- `wishlist`: Wishlist with items array
- `loading`: Loading state
- `error`: Error messages

**Actions:**
- `fetchWishlist`
- `addToWishlist`
- `removeFromWishlist`
- `clearWishlist`

## Pages

The following pages are available in the `/profile` route:

- `/profile` - Main customer profile
- `/profile/addresses` - Address management
- `/profile/wishlist` - Wishlist management
- `/profile/preferences` - Customer preferences

## API Integration

All components integrate with the backend API through the following endpoints:

**Customer Profile:**
- `GET /customer/profile/` - Fetch customer profile
- `PUT /customer/profile/` - Update customer profile
- `PUT /customer/preferences/` - Update preferences

**Addresses:**
- `GET /customer/addresses/` - Fetch addresses
- `POST /customer/addresses/` - Create address
- `PUT /customer/addresses/{id}/` - Update address
- `DELETE /customer/addresses/{id}/` - Delete address

**Wishlist:**
- `GET /wishlist/` - Fetch wishlist
- `POST /wishlist/add/` - Add to wishlist
- `DELETE /wishlist/{id}/` - Remove from wishlist
- `DELETE /wishlist/clear/` - Clear wishlist

## Styling

Components use Tailwind CSS for styling with:
- Responsive design patterns
- Consistent color scheme
- Loading states
- Error states
- Form validation styling
- Hover and focus states

## Error Handling

All components include comprehensive error handling:
- API error display
- Form validation errors
- Network error handling
- User-friendly error messages
- Toast notifications for success/error states

## Accessibility

Components follow accessibility best practices:
- Proper ARIA labels
- Keyboard navigation support
- Screen reader compatibility
- Focus management
- Semantic HTML structure