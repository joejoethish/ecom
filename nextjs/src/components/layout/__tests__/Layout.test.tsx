import React from 'react';
import { render, screen } from '@testing-library/react';
import { MainLayout } from '../MainLayout';
import AdminLayout from '../AdminLayout';
import { SellerLayout } from '../SellerLayout';
import { usePathname } from 'next/navigation';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';

// Mock the next/navigation module
jest.mock('next/navigation', () => ({
    usePathname: jest.fn(),
}));

// Mock the Breadcrumb component
jest.mock('../../common/Breadcrumb', () => ({
    Breadcrumb: () => <div data-testid="breadcrumb">Breadcrumb Component</div>,
}));

// Mock the navigation utility
jest.mock('@/utils/navigation', () => ({
    generateBreadcrumbs: jest.fn().mockReturnValue([
        { label: 'Home', href: '/' },
        { label: 'Test', href: '/test', isCurrent: true },
    ]),
}));

// Mock the Header and Footer components
jest.mock('../Header', () => ({
    Header: () => <header data-testid="header">Header Component</header>,
}));

jest.mock('../Footer', () => ({
    Footer: () => <footer data-testid="footer">Footer Component</footer>,
}));

// Mock the lucide-react icons
jest.mock('lucide-react', () => ({
    Home: () => <div>Home Icon</div>,
    Package: () => <div>Package Icon</div>,
    ShoppingCart: () => <div>ShoppingCart Icon</div>,
    User: () => <div>User Icon</div>,
    FileCheck: () => <div>FileCheck Icon</div>,
    CreditCard: () => <div>CreditCard Icon</div>,
    DollarSign: () => <div>DollarSign Icon</div>,
    BarChart3: () => <div>BarChart3 Icon</div>,
    Users: () => <div>Users Icon</div>,
    Settings: () => <div>Settings Icon</div>,
    FileText: () => <div>FileText Icon</div>,
    Activity: () => <div>Activity Icon</div>,
    Menu: () => <div>Menu Icon</div>,
    X: () => <div>X Icon</div>,
    Image: () => <div>Image Icon</div>,
    Bell: () => <div>Bell Icon</div>,
    ChevronRight: () => <div>ChevronRight Icon</div>,
}));

// Create mock store
const mockStore = configureStore([]);

describe('Layout Components', () => {
    beforeEach(() => {
        (usePathname as jest.Mock).mockReturnValue('/');
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('MainLayout', () => {
        it('renders header, footer, breadcrumb and children', () => {
            render(
                <MainLayout>
                    <div data-testid="content">Test Content</div>
                </MainLayout>
            );

            expect(screen.getByTestId('header')).toBeInTheDocument();
            expect(screen.getByTestId('footer')).toBeInTheDocument();
            expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
            expect(screen.getByTestId('content')).toBeInTheDocument();
        });
    });

    describe('AdminLayout', () => {
        it('renders sidebar, breadcrumb and children', () => {
            (usePathname as jest.Mock).mockReturnValue('/admin');

            render(
                <AdminLayout>
                    <div data-testid="content">Admin Content</div>
                </AdminLayout>
            );

            expect(screen.getByText('Admin Panel')).toBeInTheDocument();
            expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
            expect(screen.getByTestId('content')).toBeInTheDocument();
        });
    });

    describe('SellerLayout', () => {
        it('renders sidebar, breadcrumb and children', () => {
            (usePathname as jest.Mock).mockReturnValue('/seller/dashboard');

            const store = mockStore({
                seller: {
                    profile: {
                        business_name: 'Test Store',
                        verification_status: 'VERIFIED',
                        verification_status_display: 'Verified'
                    }
                }
            });

            render(
                <Provider store={store}>
                    <SellerLayout>
                        <div data-testid="content">Seller Content</div>
                    </SellerLayout>
                </Provider>
            );

            expect(screen.getByText('Seller Panel')).toBeInTheDocument();
            expect(screen.getByText('Test Store')).toBeInTheDocument();
            expect(screen.getByTestId('breadcrumb')).toBeInTheDocument();
            expect(screen.getByTestId('content')).toBeInTheDocument();
        });
    });
});