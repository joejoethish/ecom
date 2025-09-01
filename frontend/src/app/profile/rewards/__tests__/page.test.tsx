import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RewardsPage from '../page';
import { apiClient } from '@/utils/api';
import { toast } from 'react-hot-toast';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  useParams: () => ({}),
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock API client
jest.mock('@/utils/api', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockRewardsData = {
  id: '1',
  total_points_earned: 1500,
  total_points_redeemed: 500,
  current_points: 1000,
  tier: 'silver',
  tier_benefits: [
    'Basic rewards',
    'Birthday bonus',
    '5% bonus points',
  ],
  recent_transactions: [
    {
      id: '1',
      transaction_type: 'purchase',
      points: 100,
      description: 'Purchase reward',
      created_at: '2023-01-01T00:00:00Z',
    },
    {
      id: '2',
      transaction_type: 'redemption',
      points: -50,
      description: 'Redeemed for discount',
      created_at: '2023-01-02T00:00:00Z',
    },
  ],
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
};

const mockProgramData = {
  id: '1',
  name: 'VIP Rewards Program',
  description: 'Earn points with every purchase',
  points_per_dollar: 1.0,
  dollar_per_point: 0.01,
  minimum_redemption_points: 100,
  is_active: true,
};

describe('RewardsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (apiClient.get as jest.Mock).mockImplementation((url) => {
      if (url.includes('/rewards/')) {
        return Promise.resolve({ success: true, data: mockRewardsData });
      }
      if (url.includes('/program/')) {
        return Promise.resolve({ success: true, data: mockProgramData });
      }
      if (url.includes('/transactions/')) {
        return Promise.resolve({
          success: true,
          data: { results: mockRewardsData.recent_transactions },
        });
      }
      return Promise.reject(new Error('Unknown endpoint'));
    });
  });

  it('renders rewards page with data', async () => {
    render(<RewardsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('My Rewards')).toBeInTheDocument();
      expect(screen.getByText('1,000')).toBeInTheDocument(); // Current points
      expect(screen.getByText('Silver')).toBeInTheDocument(); // Tier
      expect(screen.getByText('1,500')).toBeInTheDocument(); // Lifetime earned
    });
  });

  it('displays tier benefits correctly', async () => {
    render(<RewardsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('My Rewards')).toBeInTheDocument();
    });
    
    // Click on Benefits tab
    const benefitsTab = screen.getByText('Benefits');
    fireEvent.click(benefitsTab);
    
    await waitFor(() => {
      expect(screen.getByText('Your Silver Benefits')).toBeInTheDocument();
      expect(screen.getByText('Basic rewards')).toBeInTheDocument();
      expect(screen.getByText('Birthday bonus')).toBeInTheDocument();
      expect(screen.getByText('5% bonus points')).toBeInTheDocument();
    });
  });

  it('displays transaction history', async () => {
    render(<RewardsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('My Rewards')).toBeInTheDocument();
    });
    
    // Click on History tab
    const historyTab = screen.getByText('History');
    fireEvent.click(historyTab);
    
    await waitFor(() => {
      expect(screen.getByText('Transaction History')).toBeInTheDocument();
      expect(screen.getByText('Purchase')).toBeInTheDocument();
      expect(screen.getByText('Redemption')).toBeInTheDocument();
      expect(screen.getByText('+100')).toBeInTheDocument();
      expect(screen.getByText('-50')).toBeInTheDocument();
    });
  });

  it('renders loading state', () => {
    (apiClient.get as jest.Mock).mockImplementation(() => 
      new Promise(() => {}) // Never resolves
    );
    
    render(<RewardsPage />);
    
    // Should render skeleton loaders
    expect(document.querySelectorAll('.animate-pulse')).toHaveLength(3);
  });

  it('handles API error', async () => {
    (apiClient.get as jest.Mock).mockRejectedValue(
      new Error('Failed to load rewards data')
    );
    
    render(<RewardsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Error Loading Rewards')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
    
    expect(toast.error).toHaveBeenCalledWith('Failed to load rewards data');
  });
});