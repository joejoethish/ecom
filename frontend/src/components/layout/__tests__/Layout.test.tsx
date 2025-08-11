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
jest.mock(&apos;../../common/Breadcrumb&apos;, () => ({
    Breadcrumb: () => <div data-testid="breadcrumb">Breadcrumb Component</div>,
}));

// Mock the navigation utility
jest.mock(&apos;@/utils/navigation&apos;, () => ({
    generateBreadcrumbs: jest.fn().mockReturnValue([
        { label: &apos;Home&apos;, href: &apos;/&apos; },
        { label: &apos;Test&apos;, href: &apos;/test&apos;, isCurrent: true },
    ]),
}));

// Mock the Header and Footer components
jest.mock(&apos;../Header&apos;, () => ({
    Header: () => <header data-testid="header">Header Component</header>,
}));

jest.mock(&apos;../Footer&apos;, () => ({
    Footer: () => <footer data-testid="footer">Footer Component</footer>,
}));

// Mock the lucide-react icons
jest.mock(&apos;lucide-react&apos;, () => ({
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

describe(&apos;Layout Components&apos;, () => {
    beforeEach(() => {
        (usePathname as jest.Mock).mockReturnValue(&apos;/&apos;);
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe(&apos;MainLayout&apos;, () => {
        it(&apos;renders header, footer, breadcrumb and children&apos;, () => {
            render(
                <MainLayout>
                    <div data-testid="content">Test Content</div>
                </MainLayout>
            );

            expect(screen.getByTestId(&apos;header&apos;)).toBeInTheDocument();
            expect(screen.getByTestId(&apos;footer&apos;)).toBeInTheDocument();
            expect(screen.getByTestId(&apos;breadcrumb&apos;)).toBeInTheDocument();
            expect(screen.getByTestId(&apos;content&apos;)).toBeInTheDocument();
        });
    });

    describe(&apos;AdminLayout&apos;, () => {
        it(&apos;renders sidebar, breadcrumb and children&apos;, () => {
            (usePathname as jest.Mock).mockReturnValue(&apos;/admin&apos;);

            render(
                <AdminLayout>
                    <div data-testid="content">Admin Content</div>
                </AdminLayout>
            );

            expect(screen.getByText(&apos;Admin Panel&apos;)).toBeInTheDocument();
            expect(screen.getByTestId(&apos;breadcrumb&apos;)).toBeInTheDocument();
            expect(screen.getByTestId(&apos;content&apos;)).toBeInTheDocument();
        });
    });

    describe(&apos;SellerLayout&apos;, () => {
        it(&apos;renders sidebar, breadcrumb and children&apos;, () => {
            (usePathname as jest.Mock).mockReturnValue(&apos;/seller/dashboard&apos;);

            const store = mockStore({
                seller: {
                    profile: {
                        business_name: &apos;Test Store&apos;,
                        verification_status: &apos;VERIFIED&apos;,
                        verification_status_display: &apos;Verified&apos;
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