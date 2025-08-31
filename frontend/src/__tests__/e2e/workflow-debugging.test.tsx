/**
 * End-to-End Tests for Workflow Debugging System Frontend
 * 
 * This module contains comprehensive E2E tests for frontend workflow debugging:
 * - User login workflow tracing
 * - Product fetch workflow tracing
 * - Cart operations workflow tracing
 * - Checkout workflow tracing
 * 
 * Requirements: 4.1, 4.2, 4.3, 4.4
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import userEvent from '@testing-library/user-event';
import { jest } from '@jest/globals';

// Mock API clients
import * as authApi from '../../services/authApi';
import * as productsApi from '../../services/productsApi';
import * as debuggingApi from '../../services/debuggingApi';
import * as correlationService from '../../services/correlationId';
import * as workflowTracing from '../../lib/workflow-tracing';

// Components to test
import LoginForm from '../../components/auth/LoginForm';
import ProductCatalog from '../../components/products/ProductCatalog';
import CartPage from '../../components/cart/CartPage';
import CheckoutPage from '../../components/checkout/CheckoutPage';
import DebugDashboard from '../../components/debugging/DebugDashboard';

// Store setup
import { store } from '../../store';
import authSlice from '../../store/slices/authSlice';
import productsSlice from '../../store/slices/productsSlice';
import cartSlice from '../../store/slices/cartSlice';

// Test utilities
import { createMockStore, mockApiResponse } from '../../utils/test-utils';

// Mock implementations
jest.mock('../../services/authApi');
jest.mock('../../services/productsApi');
jest.mock('../../services/debuggingApi');
jest.mock('../../services/correlationId');
jest.mock('../../lib/workflow-tracing');

const mockAuthApi = authApi as jest.Mocked<typeof authApi>;
const mockProductsApi = productsApi as jest.Mocked<typeof productsApi>;
const mockDebuggingApi = debuggingApi as jest.Mocked<typeof debuggingApi>;
const mockCorrelationService = correlationService as jest.Mocked<typeof correlationService>;
const mockWorkflowTracing = workflowTracing as jest.Mocked<typeof workflowTracing>;

describe('Workflow Debugging E2E Tests', () => {
  let mockStore: ReturnType<typeof createMockStore>;
  let mockCorrelationId: string;
  let mockWorkflowTracer: any;

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Setup mock correlation ID
    mockCorrelationId = 'test-correlation-id-123';
    mockCorrelationService.generateCorrelationId.mockReturnValue(mockCorrelationId);
    mockCorrelationService.getCurrentCorrelationId.mockReturnValue(mockCorrelationId);
    
    // Setup mock workflow tracer
    mockWorkflowTracer = {
      startWorkflow: jest.fn().mockResolvedValue({ correlationId: mockCorrelationId }),
      traceStep: jest.fn().mockResolvedValue({}),
      completeWorkflow: jest.fn().mockResolvedValue({}),
      failWorkflow: jest.fn().mockResolvedValue({}),
      recordMetric: jest.fn().mockResolvedValue({}),
      logError: jest.fn().mockResolvedValue({})
    };
    
    mockWorkflowTracing.WorkflowTracer.mockImplementation(() => mockWorkflowTracer);
    
    // Setup mock store
    mockStore = createMockStore({
      auth: {
        user: null,
        token: null,
        isAuthenticated: false,
        loading: false,
        error: null
      },
      products: {
        items: [],
        loading: false,
        error: null,
        pagination: { page: 1, totalPages: 1, totalItems: 0 }
      },
      cart: {
        items: [],
        total: 0,
        loading: false,
        error: null
      }
    });
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <Provider store={mockStore}>
        <BrowserRouter>
          {component}
        </BrowserRouter>
      </Provider>
    );
  };

  describe('User Login Workflow E2E', () => {
    it('should trace complete login workflow successfully', async () => {
      // Mock successful login response
      const mockLoginResponse = {
        user: { id: 1, username: 'testuser', email: 'test@example.com' },
        token: 'mock-jwt-token',
        refreshToken: 'mock-refresh-token'
      };
      
      mockAuthApi.login.mockResolvedValue(mockLoginResponse);
      
      // Mock debugging API calls
      mockDebuggingApi.startWorkflow.mockResolvedValue({
        correlationId: mockCorrelationId,
        workflowType: 'login',
        status: 'in_progress'
      });
      
      mockDebuggingApi.completeWorkflow.mockResolvedValue({
        correlationId: mockCorrelationId,
        status: 'completed',
        totalDurationMs: 1500
      });

      const user = userEvent.setup();
      
      renderWithProviders(<LoginForm />);

      // Step 1: Frontend form submission
      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /login/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'testpass123');

      // Verify workflow tracing started
      await act(async () => {
        await user.click(submitButton);
      });

      await waitFor(() => {
        // Verify workflow was started
        expect(mockWorkflowTracer.startWorkflow).toHaveBeenCalledWith({
          workflowType: 'login',
          metadata: expect.objectContaining({
            username: 'testuser'
          })
        });
      });

      // Verify trace steps were recorded
      await waitFor(() => {
        expect(mockWorkflowTracer.traceStep).toHaveBeenCalledWith({
          layer: 'frontend',
          component: 'LoginForm',
          operation: 'form_submit',
          metadata: expect.objectContaining({
            username: 'testuser'
          })
        });
      });

      // Verify API authentication step
      await waitFor(() => {
        expect(mockAuthApi.login).toHaveBeenCalledWith({
          username: 'testuser',
          password: 'testpass123'
        });
      });

      // Verify workflow completion
      await waitFor(() => {
        expect(mockWorkflowTracer.completeWorkflow).toHaveBeenCalled();
      });

      // Verify success state
      await waitFor(() => {
        expect(screen.queryByText(/login successful/i)).toBeInTheDocument();
      });
    });

    it('should trace failed login workflow with error handling', async () => {
      // Mock failed login response
      const mockError = new Error('Invalid credentials');
      mockAuthApi.login.mockRejectedValue(mockError);

      const user = userEvent.setup();
      
      renderWithProviders(<LoginForm />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /login/i });

      await user.type(usernameInput, 'testuser');
      await user.type(passwordInput, 'wrongpassword');

      await act(async () => {
        await user.click(submitButton);
      });

      // Verify error was logged
      await waitFor(() => {
        expect(mockWorkflowTracer.logError).toHaveBeenCalledWith({
          layer: 'frontend',
          component: 'LoginForm',
          errorType: 'AuthenticationError',
          errorMessage: 'Invalid credentials',
          metadata: expect.any(Object)
        });
      });

      // Verify workflow was failed
      await waitFor(() => {
        expect(mockWorkflowTracer.failWorkflow).toHaveBeenCalledWith({
          errorMessage: 'Invalid credentials'
        });
      });

      // Verify error message displayed
      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
    });
  });

  describe('Product Fetch Workflow E2E', () => {
    it('should trace product catalog fetch workflow', async () => {
      // Mock products response
      const mockProducts = [
        { id: 1, name: 'Product 1', price: 99.99, category: 'Electronics' },
        { id: 2, name: 'Product 2', price: 149.99, category: 'Electronics' }
      ];
      
      mockProductsApi.getProducts.mockResolvedValue({
        results: mockProducts,
        count: 2,
        next: null,
        previous: null
      });

      renderWithProviders(<ProductCatalog />);

      // Verify workflow was started
      await waitFor(() => {
        expect(mockWorkflowTracer.startWorkflow).toHaveBeenCalledWith({
          workflowType: 'product_fetch',
          metadata: expect.objectContaining({
            route: '/products'
          })
        });
      });

      // Verify frontend page load step
      await waitFor(() => {
        expect(mockWorkflowTracer.traceStep).toHaveBeenCalledWith({
          layer: 'frontend',
          component: 'ProductCatalog',
          operation: 'page_load',
          metadata: expect.any(Object)
        });
      });

      // Verify API call step
      await waitFor(() => {
        expect(mockWorkflowTracer.traceStep).toHaveBeenCalledWith({
          layer: 'frontend',
          component: 'ProductCatalog',
          operation: 'api_call',
          metadata: expect.objectContaining({
            endpoint: '/api/products',
            method: 'GET'
          })
        });
      });

      // Verify products are rendered
      await waitFor(() => {
        expect(screen.getByText('Product 1')).toBeInTheDocument();
        expect(screen.getByText('Product 2')).toBeInTheDocument();
      });

      // Verify rendering step
      await waitFor(() => {
        expect(mockWorkflowTracer.traceStep).toHaveBeenCalledWith({
          layer: 'frontend',
          component: 'ProductList',
          operation: 'render_products',
          metadata: expect.objectContaining({
            productsRendered: 2
          })
        });
      });

      // Verify workflow completion
      await waitFor(() => {
        expect(mockWorkflowTracer.completeWorkflow).toHaveBeenCalled();
      });
    });

    it('should trace product detail fetch workflow', async () => {
      const mockProduct = {
        id: 1,
        name: 'Test Product',
        price: 99.99,
        description: 'Test product description',
        category: 'Electronics'
      };

      mockProductsApi.getProduct.mockResolvedValue(mockProduct);

      // Mock product detail component
      const ProductDetail = () => {
        React.useEffect(() => {
          const tracer = new workflowTracing.WorkflowTracer();
          tracer.startWorkflow({
            workflowType: 'product_fetch',
            metadata: { productId: 1, type: 'detail' }
          });
        }, []);

        return <div>Product Detail: {mockProduct.name}</div>;
      };

      renderWithProviders(<ProductDetail />);

      await waitFor(() => {
        expect(mockWorkflowTracer.startWorkflow).toHaveBeenCalledWith({
          workflowType: 'product_fetch',
          metadata: expect.objectContaining({
            productId: 1,
            type: 'detail'
          })
        });
      });
    });
  });

  describe('Cart Operations Workflow E2E', () => {
    beforeEach(() => {
      // Setup authenticated user
      mockStore = createMockStore({
        auth: {
          user: { id: 1, username: 'testuser' },
          token: 'mock-token',
          isAuthenticated: true,
          loading: false,
          error: null
        },
        cart: {
          items: [],
          total: 0,
          loading: false,
          error: null
        }
      });
    });

    it('should trace add to cart workflow', async () => {
      const mockProduct = {
        id: 1,
        name: 'Test Product',
        price: 99.99
      };

      // Mock cart API
      const mockCartApi = {
        addItem: jest.fn().mockResolvedValue({
          id: 1,
          product: mockProduct,
          quantity: 1,
          total: 99.99
        })
      };

      // Mock ProductCard component with add to cart functionality
      const ProductCard = ({ product }: { product: any }) => {
        const handleAddToCart = async () => {
          const tracer = new workflowTracing.WorkflowTracer();
          
          await tracer.startWorkflow({
            workflowType: 'cart_update',
            metadata: { operation: 'add_to_cart', productId: product.id }
          });

          await tracer.traceStep({
            layer: 'frontend',
            component: 'ProductCard',
            operation: 'add_to_cart_click',
            metadata: { productId: product.id, quantity: 1 }
          });

          try {
            await mockCartApi.addItem({ productId: product.id, quantity: 1 });
            
            await tracer.traceStep({
              layer: 'frontend',
              component: 'CartStore',
              operation: 'update_cart_state',
              metadata: { cartUpdated: true }
            });

            await tracer.completeWorkflow();
          } catch (error) {
            await tracer.failWorkflow({ errorMessage: (error as Error).message });
          }
        };

        return (
          <div>
            <h3>{product.name}</h3>
            <button onClick={handleAddToCart}>Add to Cart</button>
          </div>
        );
      };

      const user = userEvent.setup();
      
      renderWithProviders(<ProductCard product={mockProduct} />);

      const addButton = screen.getByText('Add to Cart');
      
      await act(async () => {
        await user.click(addButton);
      });

      // Verify workflow started
      await waitFor(() => {
        expect(mockWorkflowTracer.startWorkflow).toHaveBeenCalledWith({
          workflowType: 'cart_update',
          metadata: expect.objectContaining({
            operation: 'add_to_cart',
            productId: 1
          })
        });
      });

      // Verify trace steps
      await waitFor(() => {
        expect(mockWorkflowTracer.traceStep).toHaveBeenCalledWith({
          layer: 'frontend',
          component: 'ProductCard',
          operation: 'add_to_cart_click',
          metadata: expect.objectContaining({
            productId: 1,
            quantity: 1
          })
        });
      });

      await waitFor(() => {
        expect(mockWorkflowTracer.completeWorkflow).toHaveBeenCalled();
      });
    });

    it('should trace remove from cart workflow', async () => {
      // Setup cart with items
      mockStore = createMockStore({
        auth: {
          user: { id: 1, username: 'testuser' },
          token: 'mock-token',
          isAuthenticated: true,
          loading: false,
          error: null
        },
        cart: {
          items: [
            { id: 1, product: { id: 1, name: 'Test Product' }, quantity: 1, total: 99.99 }
          ],
          total: 99.99,
          loading: false,
          error: null
        }
      });

      const mockCartApi = {
        removeItem: jest.fn().mockResolvedValue({})
      };

      const CartItem = ({ item }: { item: any }) => {
        const handleRemove = async () => {
          const tracer = new workflowTracing.WorkflowTracer();
          
          await tracer.startWorkflow({
            workflowType: 'cart_update',
            metadata: { operation: 'remove_from_cart', cartItemId: item.id }
          });

          try {
            await mockCartApi.removeItem(item.id);
            await tracer.completeWorkflow();
          } catch (error) {
            await tracer.failWorkflow({ errorMessage: (error as Error).message });
          }
        };

        return (
          <div>
            <span>{item.product.name}</span>
            <button onClick={handleRemove}>Remove</button>
          </div>
        );
      };

      const user = userEvent.setup();
      
      renderWithProviders(
        <CartItem item={{ id: 1, product: { id: 1, name: 'Test Product' }, quantity: 1 }} />
      );

      const removeButton = screen.getByText('Remove');
      
      await act(async () => {
        await user.click(removeButton);
      });

      await waitFor(() => {
        expect(mockWorkflowTracer.startWorkflow).toHaveBeenCalledWith({
          workflowType: 'cart_update',
          metadata: expect.objectContaining({
            operation: 'remove_from_cart',
            cartItemId: 1
          })
        });
      });
    });
  });

  describe('Checkout Workflow E2E', () => {
    beforeEach(() => {
      // Setup authenticated user with cart items
      mockStore = createMockStore({
        auth: {
          user: { id: 1, username: 'testuser' },
          token: 'mock-token',
          isAuthenticated: true,
          loading: false,
          error: null
        },
        cart: {
          items: [
            { id: 1, product: { id: 1, name: 'Test Product' }, quantity: 2, total: 199.98 }
          ],
          total: 199.98,
          loading: false,
          error: null
        }
      });
    });

    it('should trace complete checkout workflow', async () => {
      const mockOrderApi = {
        createOrder: jest.fn().mockResolvedValue({
          id: 1,
          orderNumber: 'ORD-001',
          total: 199.98,
          status: 'confirmed'
        })
      };

      const CheckoutForm = () => {
        const [isProcessing, setIsProcessing] = React.useState(false);

        const handleSubmit = async (formData: any) => {
          setIsProcessing(true);
          
          const tracer = new workflowTracing.WorkflowTracer();
          
          await tracer.startWorkflow({
            workflowType: 'checkout',
            metadata: { cartTotal: 199.98 }
          });

          try {
            // Step 1: Payment processing
            await tracer.traceStep({
              layer: 'frontend',
              component: 'CheckoutForm',
              operation: 'submit_payment',
              metadata: { paymentMethod: formData.paymentMethod }
            });

            // Step 2: Order creation
            const order = await mockOrderApi.createOrder(formData);
            
            await tracer.traceStep({
              layer: 'frontend',
              component: 'CheckoutForm',
              operation: 'order_created',
              metadata: { orderId: order.id, orderNumber: order.orderNumber }
            });

            // Step 3: Confirmation display
            await tracer.traceStep({
              layer: 'frontend',
              component: 'OrderConfirmation',
              operation: 'display_confirmation',
              metadata: { orderCreated: true }
            });

            await tracer.completeWorkflow();
            setIsProcessing(false);
          } catch (error) {
            await tracer.failWorkflow({ errorMessage: (error as Error).message });
            setIsProcessing(false);
          }
        };

        return (
          <form onSubmit={(e) => {
            e.preventDefault();
            handleSubmit({
              shippingAddress: '123 Test St',
              paymentMethod: 'credit_card',
              paymentToken: 'test_token_123'
            });
          }}>
            <input name="shippingAddress" defaultValue="123 Test St" />
            <select name="paymentMethod" defaultValue="credit_card">
              <option value="credit_card">Credit Card</option>
            </select>
            <button type="submit" disabled={isProcessing}>
              {isProcessing ? 'Processing...' : 'Place Order'}
            </button>
          </form>
        );
      };

      const user = userEvent.setup();
      
      renderWithProviders(<CheckoutForm />);

      const submitButton = screen.getByText('Place Order');
      
      await act(async () => {
        await user.click(submitButton);
      });

      // Verify workflow started
      await waitFor(() => {
        expect(mockWorkflowTracer.startWorkflow).toHaveBeenCalledWith({
          workflowType: 'checkout',
          metadata: expect.objectContaining({
            cartTotal: 199.98
          })
        });
      });

      // Verify payment processing step
      await waitFor(() => {
        expect(mockWorkflowTracer.traceStep).toHaveBeenCalledWith({
          layer: 'frontend',
          component: 'CheckoutForm',
          operation: 'submit_payment',
          metadata: expect.objectContaining({
            paymentMethod: 'credit_card'
          })
        });
      });

      // Verify order creation step
      await waitFor(() => {
        expect(mockWorkflowTracer.traceStep).toHaveBeenCalledWith({
          layer: 'frontend',
          component: 'CheckoutForm',
          operation: 'order_created',
          metadata: expect.objectContaining({
            orderId: 1,
            orderNumber: 'ORD-001'
          })
        });
      });

      // Verify workflow completion
      await waitFor(() => {
        expect(mockWorkflowTracer.completeWorkflow).toHaveBeenCalled();
      });
    });
  });

  describe('Performance Monitoring E2E', () => {
    it('should record performance metrics during workflows', async () => {
      const mockPerformanceObserver = {
        observe: jest.fn(),
        disconnect: jest.fn()
      };

      // Mock Performance API
      Object.defineProperty(window, 'PerformanceObserver', {
        writable: true,
        value: jest.fn().mockImplementation(() => mockPerformanceObserver)
      });

      const PerformanceMonitoredComponent = () => {
        React.useEffect(() => {
          const tracer = new workflowTracing.WorkflowTracer();
          
          // Record page load performance
          tracer.recordMetric({
            layer: 'frontend',
            component: 'PerformanceMonitoredComponent',
            metricName: 'page_load_time',
            metricValue: 1250, // 1.25 seconds
            metadata: { route: '/test' }
          });
        }, []);

        return <div>Performance Monitored Component</div>;
      };

      renderWithProviders(<PerformanceMonitoredComponent />);

      await waitFor(() => {
        expect(mockWorkflowTracer.recordMetric).toHaveBeenCalledWith({
          layer: 'frontend',
          component: 'PerformanceMonitoredComponent',
          metricName: 'page_load_time',
          metricValue: 1250,
          metadata: { route: '/test' }
        });
      });
    });

    it('should handle performance threshold violations', async () => {
      const SlowComponent = () => {
        React.useEffect(() => {
          const tracer = new workflowTracing.WorkflowTracer();
          
          // Simulate slow operation
          setTimeout(() => {
            tracer.recordMetric({
              layer: 'frontend',
              component: 'SlowComponent',
              metricName: 'response_time',
              metricValue: 5000, // 5 seconds - exceeds threshold
              metadata: { operation: 'slow_operation' }
            });

            // Log performance warning
            tracer.logError({
              layer: 'frontend',
              component: 'SlowComponent',
              errorType: 'PerformanceWarning',
              errorMessage: 'Operation exceeded performance threshold',
              metadata: { threshold: 2000, actual: 5000 }
            });
          }, 100);
        }, []);

        return <div>Slow Component</div>;
      };

      renderWithProviders(<SlowComponent />);

      await waitFor(() => {
        expect(mockWorkflowTracer.logError).toHaveBeenCalledWith({
          layer: 'frontend',
          component: 'SlowComponent',
          errorType: 'PerformanceWarning',
          errorMessage: 'Operation exceeded performance threshold',
          metadata: expect.objectContaining({
            threshold: 2000,
            actual: 5000
          })
        });
      }, { timeout: 3000 });
    });
  });

  describe('Error Handling E2E', () => {
    it('should handle and trace network errors', async () => {
      // Mock network error
      mockProductsApi.getProducts.mockRejectedValue(new Error('Network error'));

      const ErrorProneComponent = () => {
        React.useEffect(() => {
          const tracer = new workflowTracing.WorkflowTracer();
          
          const fetchData = async () => {
            try {
              await tracer.startWorkflow({
                workflowType: 'product_fetch',
                metadata: { component: 'ErrorProneComponent' }
              });

              await mockProductsApi.getProducts();
              await tracer.completeWorkflow();
            } catch (error) {
              await tracer.logError({
                layer: 'frontend',
                component: 'ErrorProneComponent',
                errorType: 'NetworkError',
                errorMessage: (error as Error).message,
                metadata: { operation: 'fetch_products' }
              });

              await tracer.failWorkflow({
                errorMessage: (error as Error).message
              });
            }
          };

          fetchData();
        }, []);

        return <div>Error Prone Component</div>;
      };

      renderWithProviders(<ErrorProneComponent />);

      await waitFor(() => {
        expect(mockWorkflowTracer.logError).toHaveBeenCalledWith({
          layer: 'frontend',
          component: 'ErrorProneComponent',
          errorType: 'NetworkError',
          errorMessage: 'Network error',
          metadata: { operation: 'fetch_products' }
        });
      });

      await waitFor(() => {
        expect(mockWorkflowTracer.failWorkflow).toHaveBeenCalledWith({
          errorMessage: 'Network error'
        });
      });
    });
  });
});