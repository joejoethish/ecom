import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import NotificationBell from '../NotificationBell';
import notificationReducer from '@/store/slices/notificationSlice';

// Mock store
const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      notifications: notificationReducer,
    },
    preloadedState: {
      notifications: {
        notifications: [],
        currentNotification: null,
        unreadCount: 0,
        preferences: [],
        settings: null,
        stats: null,
        isNotificationCenterOpen: false,
        filters: {},
        loading: {
          notifications: false,
          preferences: false,
          stats: false,
          settings: false,
          markingAsRead: false,
          updatingPreferences: false,
        },
        error: {
          notifications: null,
          preferences: null,
          stats: null,
          settings: null,
          markingAsRead: null,
          updatingPreferences: null,
        },
        ...initialState,
      },
    },
  });
};

describe('NotificationBell', () => {
  it('renders without crashing', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <NotificationBell />
      </Provider>
    );
    
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('shows unread count badge when there are unread notifications', () => {
    const store = createMockStore({
      unreadCount: 5,
    });
    
    render(
      <Provider store={store}>
        <NotificationBell />
      </Provider>
    );
    
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('does not show badge when showBadge is false', () => {
    const store = createMockStore({
      unreadCount: 5,
    });
    
    render(
      <Provider store={store}>
        <NotificationBell showBadge={false} />
      </Provider>
    );
    
    expect(screen.queryByText('5')).not.toBeInTheDocument();
  });

  it('shows 99+ when unread count exceeds 99', () => {
    const store = createMockStore({
      unreadCount: 150,
    });
    
    render(
      <Provider store={store}>
        <NotificationBell />
      </Provider>
    );
    
    expect(screen.getByText('99+')).toBeInTheDocument();
  });

  it('toggles notification center when clicked', () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <NotificationBell />
      </Provider>
    );
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    // Check if the notification center state changed
    const state = store.getState();
    expect(state.notifications.isNotificationCenterOpen).toBe(true);
  });

  it('has correct accessibility attributes', () => {
    const store = createMockStore({
      unreadCount: 3,
    });
    
    render(
      <Provider store={store}>
        <NotificationBell />
      </Provider>
    );
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Notifications (3 unread)');
  });

  it('applies correct size classes', () => {
    const store = createMockStore();
    
    const { rerender } = render(
      <Provider store={store}>
        <NotificationBell size="sm" />
      </Provider>
    );
    
    let button = screen.getByRole('button');
    expect(button).toHaveClass('h-8', 'w-8');
    
    rerender(
      <Provider store={store}>
        <NotificationBell size="lg" />
      </Provider>
    );
    
    button = screen.getByRole('button');
    expect(button).toHaveClass('h-12', 'w-12');
  });
});